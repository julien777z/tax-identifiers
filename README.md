# tax-validation

Country-aware tax identifier validation, normalization, and metadata resolution for Pydantic models.

## Installation

```bash
pip install tax-validation
```

## Quick Start

Construct a `TaxValidator` for a country and validate an identifier — the validator normalizes the value, applies that country's structural rules, and resolves any metadata. Currently, only the US validators have dedicated validation rules; every other country falls back to generic normalization.

```python
from tax_validation import TaxValidator, Country, TaxIdentifierType

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

Only countries with dedicated rules can be validated. Rather than guess, validating a country the library has no rules for raises `NotImplementedError`:

```python
TaxValidator(Country.from_string("France")).validate(
    "FR1234567", TaxIdentifierType.FOREIGN_TIN
)   # raises NotImplementedError — no validation rules for France
```

An unrecognized country string raises `UnknownCountryError`:

```python
Country.from_string("Atlantis")   # raises UnknownCountryError
```

## Raising vs. Returning

`validate` raises on malformed or unsupported input. A parseable-but-reserved identifier is *not* an error — it comes back with `valid=False`:

```python
from tax_validation import InvalidTaxIdError, UnsupportedTaxIdTypeError

validator.validate("666-12-3456", TaxIdentifierType.SSN).valid          # False — 666 is a reserved area
validator.validate("123-45-67890", TaxIdentifierType.SSN)               # raises InvalidTaxIdError — 10 digits
TaxValidator(Country.US).validate("X1", TaxIdentifierType.FOREIGN_TIN)  # raises UnsupportedTaxIdTypeError
```

`TaxValidationResult.from_tax_identifier` is the non-raising counterpart — it returns `None` for missing or malformed input instead of raising:

```python
from tax_validation import TaxValidationResult

summary = TaxValidationResult.from_tax_identifier(
    country=Country.US, tax_id="12-3456789", tax_id_type=TaxIdentifierType.EIN
)
summary.valid   # True
```

## Normalization Utilities

Reusable normalization helpers and annotated Pydantic field types you can drop into your own models:

```python
from tax_validation import clean_us_tax_identifier, format_us_ssn, format_us_ein, ComparableUsTaxIdentifier

clean_us_tax_identifier(" 123-45-6789 ")                  # "123456789"
format_us_ssn("123456789")                                # "123-45-6789"
format_us_ein("123456789")                                # "12-3456789"
ComparableUsTaxIdentifier("123-45-6789") == "123456789"   # True — equality ignores formatting
```

`NormalizedString` and `StringBool` are configurable annotated field types:

```python
from tax_validation import BaseModel, NormalizedString, StringBool


def is_yes(value: str) -> bool:
    return value.strip().upper() in {"YES", "Y"}


class IntakeForm(BaseModel):
    business_name: NormalizedString(normalize_to_uppercase=True)
    consented: StringBool(predicate=is_yes)


form = IntakeForm(business_name="  acme llc ", consented="yes")
form.business_name   # "ACME LLC"
form.consented       # True
```

`NormalizedString` collapses internal and edge whitespace first, then applies any of:

| Option | Effect |
|--------|--------|
| `normalize_to_uppercase` | Uppercase the value |
| `normalize_to_lowercase` | Lowercase the value |
| `normalize_to_titlecase` | Title-case the value |
| `strip_non_digits` | Remove every non-digit character |
| `strip_trailing_punctuation` | Drop trailing `.` and `,` from each token |

## Masking Tax Identifiers

A `TaxIdField` carries a country and identifier type and normalizes on construction. Mix in `TaxIdentifierPairMixin` to mask the value while keeping the original recoverable:

```python
from tax_validation import BaseModel, Country, TaxIdentifierPairMixin, TaxIdentifierType, TaxIdField


class ContractorTaxInfo(TaxIdentifierPairMixin, BaseModel):
    name: str
    tax_id: TaxIdField(country=Country.US, tax_id_type=TaxIdentifierType.SSN)


record = ContractorTaxInfo(name="Jane Doe", tax_id="123-45-6789")
record.tax_id == "123456789"   # normalized on construction — equality ignores formatting

masked = record.to_masked()
masked.tax_id                  # "*******6789"
masked.to_unmask().tax_id      # "123-45-6789" — original recovered
```

## Run Tests

```bash
pip install -e ".[dev]"
pytest -v
```
