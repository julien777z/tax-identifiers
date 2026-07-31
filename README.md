# Tax Identifiers

Country-aware tax identifier validation, normalization, and metadata resolution for Pydantic models.

## Features

- Validate US tax identifiers against SSN, EIN and ITIN structural rules, with generic normalization for every other country.
- Resolve SSN allocation metadata: issuing state and issued years.
- Annotated Pydantic field types that normalize a tax identifier on construction and reject one its country's rules find invalid.
- Masking and unmasking of tax identifier fields, with the original recoverable.
- Country resolution from ISO codes, alpha-3 codes and full names.
- Typed throughout, with a PEP 561 `py.typed` marker.

## Installation

```bash
pip install tax-identifiers
```

## Typing

Every field type this package exports is a plain `Annotated` alias, valid in annotation position:

```python
from pydantic import BaseModel

from tax_identifiers import SSNTaxIdField


class TaxPayer(BaseModel):
    tax_id: SSNTaxIdField
```

Configuration lives in metadata objects inside `Annotated`, so a field type is always a name you can annotate with, never a call.

## Quick Start

Construct a `TaxValidator` for a country and validate an identifier. The validator normalizes the value, applies that country's structural rules, and resolves any metadata. Currently, only the US validators have dedicated validation rules; every other country falls back to generic normalization.

```python
from tax_identifiers import TaxValidator, Country, TaxIdentifierType

validator = TaxValidator(Country.US)
result = validator.validate("123-45-6789", TaxIdentifierType.SSN)

result.valid                   # True, passes the SSN reserved-range checks
result.country                 # Country.US
result.tax_id_type             # TaxIdentifierType.SSN
result.metadata.issued_state   # a USState enum, e.g. USState.NEW_YORK ("NY")
result.metadata.issued_years   # e.g. "1936-1950"
```

`TaxValidationResult` omits the raw identifier.

## Resolving Countries

`Country.from_string` normalizes codes and names, so `"US"`, `"us"`, `"United States"`, and `"USA"` all resolve to `Country.US`. A validator can be built straight from a stored country string:

```python
validator = TaxValidator(Country.from_string(row.country))   # ISO code or full name
```

A **named** country without dedicated rules can't decide validity, so it reports `valid` as `None` rather than guessing:

```python
TaxValidator(Country.from_string("France")).validate(
    "FR1234567", TaxIdentifierType.FOREIGN_TIN
).valid   # None, no validation rules for France
```

`Country.UNKNOWN` is the country-agnostic exception: it accepts any non-empty identifier, so foreign identifiers of any shape validate against it.

An unrecognized country string raises `UnknownCountryError`:

```python
Country.from_string("Atlantis")   # raises UnknownCountryError
```

## Error Handling

`validate` raises on malformed or unsupported input. A parseable-but-reserved identifier is *not* an error. It comes back with `valid=False`, and a country whose rules cannot decide comes back with `valid=None`:

```python
from tax_identifiers import InvalidTaxIdError, UnsupportedTaxIdTypeError

validator.validate("666-12-3456", TaxIdentifierType.SSN).valid          # False, 666 is a reserved area
validator.validate("123-45-67890", TaxIdentifierType.SSN)               # raises InvalidTaxIdError, 10 digits
TaxValidator(Country.US).validate("X1", TaxIdentifierType.FOREIGN_TIN)  # raises UnsupportedTaxIdTypeError
```

Each country handles a fixed set of identifier types, so a field declared with a pair its country does not handle raises `UnsupportedTaxIdTypeError` when the model class is built, not when a value arrives.

`TaxValidationResult.from_tax_identifier` returns `None` for missing or malformed input instead of raising:

```python
from tax_identifiers import TaxValidationResult

summary = TaxValidationResult.from_tax_identifier(
    country=Country.US, tax_id="12-3456789", tax_id_type=TaxIdentifierType.EIN
)
summary.valid   # True
```

## Normalization Utilities

```python
from tax_identifiers import clean_us_tax_identifier, format_us_ssn, format_us_ein, ComparableUsTaxIdentifier

clean_us_tax_identifier(" 123-45-6789 ")                  # "123456789"
format_us_ssn("123456789")                                # "123-45-6789"
format_us_ein("123456789")                                # "12-3456789"
ComparableUsTaxIdentifier("123-45-6789") == "123456789"   # True, equality ignores formatting
```

## Masking Tax Identifiers

A tax ID field carries a country and identifier type and normalizes on construction. `TaxIdentifierPairMixin` masks the value while keeping the original recoverable; it reads annotation metadata through `get_annotated_fields`, so it is mixed into a `SuperModelPydanticMixin` model:

```python
from pydantic_super_model import SuperModelPydanticMixin

from tax_identifiers import SSNTaxIdField, TaxIdentifierPairMixin


class TaxPayer(TaxIdentifierPairMixin, SuperModelPydanticMixin):
    name: str
    tax_id: SSNTaxIdField


record = TaxPayer(name="Jane Doe", tax_id="123-45-6789")
record.tax_id == "123456789"   # normalized on construction

masked = record.to_masked()
masked.tax_id                  # "*******6789"
masked.to_unmask().tax_id      # "123-45-6789", original recovered
```

A field rejects a value its country's rules find structurally invalid, raising `InvalidTaxIdError`. Because that subclasses `ValueError`, pydantic reports it as a `ValidationError` like any other field failure. A country whose rules cannot decide validity rejects nothing, so today that means `SSNTaxIdField` rejects reserved SSN ranges and the other aliases accept whatever normalizes.

`LenientSSNTaxIdField` normalizes and carries the same SSN metadata but does not reject, for parsing payloads from a third party whose values you do not control. Any annotation can opt out the same way with `TaxIdFieldOptions(..., assert_validity=False)`.

The shipped aliases, each naming a country and an identifier type. Every one rejects a value that is already masked.

| Alias | Country | Type |
|-------|---------|------|
| `SSNTaxIdField` | US | SSN |
| `LenientSSNTaxIdField` | US | SSN |
| `USTaxIdField` | US | unspecified |
| `ForeignTaxIdField` | `UNKNOWN` | foreign TIN |
| `UnknownTaxIdField` | `UNKNOWN` | none |

A field that reads a value back from storage already masked, such as `"*****6789"`, adds `AllowMasked`:

```python
from typing import Annotated

from pydantic import BaseModel

from tax_identifiers import AllowMasked, USTaxIdField


class StoredTaxPayer(BaseModel):
    tax_id: Annotated[USTaxIdField, AllowMasked]
```

`AllowMasked` composes with any alias or custom annotation, so masking stays one marker rather than a variant of every name. A masked value is returned untouched, skipping normalization and the validity check.

Leniency is a field option rather than a marker because it is a decision inside the validity check, not a test on the raw input: `LenientSSNTaxIdField` carries the same SSN country and type metadata but does not reject.

For any other combination, put `TaxIdFieldOptions` inside an `Annotated`:

```python
from typing import Annotated

from tax_identifiers import Country, TaxIdentifierType, TaxIdFieldOptions, TaxIdStr

FrenchTinField = Annotated[
    TaxIdStr,
    TaxIdFieldOptions(country=Country.FR, tax_id_type=TaxIdentifierType.FOREIGN_TIN),
]
```

`TaxIdFieldOptions` defaults to `Country.UNKNOWN` with `TaxIdentifierType.NONE`, a country-agnostic field that normalizes (uppercases) and accepts any non-empty value. Pass `country=Country.US` to apply a country's rules, along with a `tax_id_type` that country handles.

## Local Development

```bash
poetry install --all-extras   # install
poetry run pytest             # run the tests
poetry run black .            # format
poetry run pyright            # type check
```
