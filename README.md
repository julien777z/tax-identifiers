# tax-identifiers

Country-aware tax identifier validation, normalization, and metadata resolution for Pydantic models.

## Installation

```bash
pip install tax-identifiers
```

## Typing

Every field type this package exports is a plain `Annotated` alias, valid in annotation position:

```python
from tax_identifiers import BaseModel, SSNTaxIdField


class Contractor(BaseModel):
    tax_id: SSNTaxIdField
```

Configuration lives in metadata objects inside `Annotated`, so a field type is always a name you can annotate with — never a call. The package ships a PEP 561 `py.typed` marker, and pyright checks the whole package plus its test suite in CI.

## Quick Start

Construct a `TaxValidator` for a country and validate an identifier — the validator normalizes the value, applies that country's structural rules, and resolves any metadata. Currently, only the US validators have dedicated validation rules; every other country falls back to generic normalization.

```python
from tax_identifiers import TaxValidator, Country, TaxIdentifierType

validator = TaxValidator(Country.US)
result = validator.validate("123-45-6789", TaxIdentifierType.SSN)

result.valid                   # True — passes the SSN reserved-range checks
result.country                 # Country.US
result.tax_id_type             # TaxIdentifierType.SSN
result.metadata.issued_state   # a USState enum — e.g. USState.NEW_YORK ("NY")
result.metadata.issued_years   # e.g. "1936-1950"
```

`TaxValidationResult` omits the raw identifier, so it is safe to log or return from an API.

## Resolving Countries

`Country.from_string` normalizes codes and names — `"US"`, `"us"`, `"United States"`, and `"USA"` all resolve to `Country.US` — so a validator can be built straight from a stored country string:

```python
validator = TaxValidator(Country.from_string(row.country))   # ISO code or full name
```

A **named** country without dedicated rules can't assert validity — its validator raises `NotImplementedError`:

```python
TaxValidator(Country.from_string("France")).validate(
    "FR1234567", TaxIdentifierType.FOREIGN_TIN
)   # raises NotImplementedError — no validation rules for France
```

`Country.UNKNOWN` is the country-agnostic exception: it accepts any non-empty identifier, so foreign identifiers of any shape validate against it.

An unrecognized country string raises `UnknownCountryError`:

```python
Country.from_string("Atlantis")   # raises UnknownCountryError
```

## Error Handling

`validate` raises on malformed or unsupported input. A parseable-but-reserved identifier is *not* an error — it comes back with `valid=False`:

```python
from tax_identifiers import InvalidTaxIdError, UnsupportedTaxIdTypeError

validator.validate("666-12-3456", TaxIdentifierType.SSN).valid          # False — 666 is a reserved area
validator.validate("123-45-67890", TaxIdentifierType.SSN)               # raises InvalidTaxIdError — 10 digits
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

Reusable normalization helpers and annotated Pydantic field types you can drop into your own models:

```python
from tax_identifiers import clean_us_tax_identifier, format_us_ssn, format_us_ein, ComparableUsTaxIdentifier

clean_us_tax_identifier(" 123-45-6789 ")                  # "123456789"
format_us_ssn("123456789")                                # "123-45-6789"
format_us_ein("123456789")                                # "12-3456789"
ComparableUsTaxIdentifier("123-45-6789") == "123456789"   # True — equality ignores formatting
```

`build_string_normalizer` builds a normalizer you can attach with pydantic's own `AfterValidator`:

```python
from typing import Annotated

from pydantic import AfterValidator

from tax_identifiers import BaseModel, build_string_normalizer

BusinessName = Annotated[str, AfterValidator(build_string_normalizer(normalize_to_uppercase=True))]


class IntakeForm(BaseModel):
    business_name: BusinessName


IntakeForm(business_name="  acme llc ").business_name   # "ACME LLC"
```

`build_string_normalizer` collapses internal and edge whitespace first, then applies any of:

| Option | Effect |
|--------|--------|
| `normalize_to_uppercase` | Uppercase the value |
| `normalize_to_lowercase` | Lowercase the value |
| `normalize_to_titlecase` | Title-case the value |
| `strip_non_digits` | Remove every non-digit character |
| `strip_trailing_punctuation` | Drop trailing `.` and `,` from each token |

## Masking Tax Identifiers

A tax ID field carries a country and identifier type and normalizes on construction. Mix in `TaxIdentifierPairMixin` to mask the value while keeping the original recoverable:

```python
from tax_identifiers import BaseModel, SSNTaxIdField, TaxIdentifierPairMixin


class ContractorTaxInfo(TaxIdentifierPairMixin, BaseModel):
    name: str
    tax_id: SSNTaxIdField


record = ContractorTaxInfo(name="Jane Doe", tax_id="123-45-6789")
record.tax_id == "123456789"   # normalized on construction — equality ignores formatting

masked = record.to_masked()
masked.tax_id                  # "*******6789"
masked.to_unmask().tax_id      # "123-45-6789" — original recovered
```

The shipped aliases:

| Alias | Country | Type | Maskable twin |
|-------|---------|------|---------------|
| `SSNTaxIdField` | US | SSN | — |
| `USTaxIdField` | US | unspecified | `MaskableUSTaxIdField` |
| `ForeignTaxIdField` | `UNKNOWN` | foreign TIN | `MaskableForeignTaxIdField` |
| `UnknownTaxIdField` | `UNKNOWN` | unspecified | `MaskableUnknownTaxIdField` |

A `Maskable` twin accepts already-masked input; the plain alias rejects it.

For any other combination, put `TaxIdFieldOptions` inside an `Annotated`:

```python
from typing import Annotated

from tax_identifiers import Country, TaxIdentifierType, TaxIdFieldOptions, TaxIdStr

FrenchTinField = Annotated[
    TaxIdStr,
    TaxIdFieldOptions(country=Country.FR, tax_id_type=TaxIdentifierType.FOREIGN_TIN),
]
```

`TaxIdFieldOptions` defaults to `Country.UNKNOWN` — a country-agnostic field that normalizes (uppercases) but is never validated. Pass `country=Country.US` to apply a country's rules.

## Run Tests

```bash
pip install -e ".[dev]"
pytest -v
```
