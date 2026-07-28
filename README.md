# Tax Identifiers

Country-aware tax identifier validation, normalization, and metadata resolution for Pydantic models.

## Features

- Validate US tax identifiers against SSN, EIN and ITIN structural rules, with generic normalization for every other country.
- Resolve SSN allocation metadata: issuing state and issued years.
- Annotated Pydantic field types that normalize a tax identifier on construction.
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


class Contractor(BaseModel):
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

A **named** country without dedicated rules can't assert validity, so its validator raises `NotImplementedError`:

```python
TaxValidator(Country.from_string("France")).validate(
    "FR1234567", TaxIdentifierType.FOREIGN_TIN
)   # raises NotImplementedError, no validation rules for France
```

`Country.UNKNOWN` is the country-agnostic exception: it accepts any non-empty identifier, so foreign identifiers of any shape validate against it.

An unrecognized country string raises `UnknownCountryError`:

```python
Country.from_string("Atlantis")   # raises UnknownCountryError
```

## Error Handling

`validate` raises on malformed or unsupported input. A parseable-but-reserved identifier is *not* an error. It comes back with `valid=False`:

```python
from tax_identifiers import InvalidTaxIdError, UnsupportedTaxIdTypeError

validator.validate("666-12-3456", TaxIdentifierType.SSN).valid          # False, 666 is a reserved area
validator.validate("123-45-67890", TaxIdentifierType.SSN)               # raises InvalidTaxIdError, 10 digits
TaxValidator(Country.US).validate("X1", TaxIdentifierType.FOREIGN_TIN)  # raises UnsupportedTaxIdTypeError
```

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


class ContractorTaxInfo(TaxIdentifierPairMixin, SuperModelPydanticMixin):
    name: str
    tax_id: SSNTaxIdField


record = ContractorTaxInfo(name="Jane Doe", tax_id="123-45-6789")
record.tax_id == "123456789"   # normalized on construction

masked = record.to_masked()
masked.tax_id                  # "*******6789"
masked.to_unmask().tax_id      # "123-45-6789", original recovered
```

The shipped aliases. A `Maskable` name accepts a value that is already masked, such as `"*****6789"` read back from storage; the others reject one.

| Alias | Country | Type | Accepts masked input |
|-------|---------|------|----------------------|
| `SSNTaxIdField` | US | SSN | no |
| `USTaxIdField` | US | unspecified | no |
| `ForeignTaxIdField` | `UNKNOWN` | foreign TIN | no |
| `UnknownTaxIdField` | `UNKNOWN` | unspecified | no |
| `MaskableUSTaxIdField` | US | unspecified | yes |
| `MaskableForeignTaxIdField` | `UNKNOWN` | foreign TIN | yes |
| `MaskableUnknownTaxIdField` | `UNKNOWN` | unspecified | yes |

For any other combination, put `TaxIdFieldOptions` inside an `Annotated`:

```python
from typing import Annotated

from tax_identifiers import Country, TaxIdentifierType, TaxIdFieldOptions, TaxIdStr

FrenchTinField = Annotated[
    TaxIdStr,
    TaxIdFieldOptions(country=Country.FR, tax_id_type=TaxIdentifierType.FOREIGN_TIN),
]
```

`TaxIdFieldOptions` defaults to `Country.UNKNOWN`, a country-agnostic field that normalizes (uppercases) but is never validated. Pass `country=Country.US` to apply a country's rules.

## Local Development

```bash
poetry install --all-extras   # install
poetry run pytest             # run the tests
poetry run black .            # format
poetry run pyright            # type check
```
