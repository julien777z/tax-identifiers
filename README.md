# tax-validation

Validate tax identifiers and resolve their metadata with Pydantic. The library
normalizes tax IDs, rejects values that do not conform to their country's
structural rules, and returns resolved details such as an SSN's issuing state and
issued years. The United States has dedicated rules; every other country is
accepted with generic normalization and validation.

## Installation

```bash
pip install tax-validation
```

## Quick start

```python
from tax_validation import TaxValidator, Country, TaxIdentifierType

validator = TaxValidator(Country.US)

result = validator.validate("123-45-6789", TaxIdentifierType.SSN)
result.valid                   # True (passes reserved-range checks)
result.country                 # Country.US
result.tax_id_type             # TaxIdentifierType.SSN
result.metadata.issued_state   # a USState enum (serializes to e.g. "NY")
result.metadata.issued_years   # e.g. "1936-1950"
```

`Country.from_string` normalizes codes and names (`"US"`, `"us"`, `"United States"`,
`"USA"`, …), so a validator can be built straight from a database column:

```python
validator = TaxValidator(Country.from_string(row.country))
```

Countries without dedicated rules fall back to generic normalization and a
plausibility check, while still reporting the resolved country:

```python
validator = TaxValidator(Country.from_string("France"))

result = validator.validate("FR1234567", TaxIdentifierType.FOREIGN_TIN)
result.country    # Country.FR
result.valid      # True (generic sanity check)
result.metadata   # None (no country-specific metadata)
```

`validate` raises when the identifier is structurally malformed or its type is
unsupported for the country; otherwise it returns a `TaxValidationResult` summary
(which omits the raw identifier) whose `valid` flag reflects the structural checks:

```python
from tax_validation import InvalidTaxIdError, UnsupportedTaxIdTypeError

# A parseable SSN returns a summary; reserved ranges set valid=False (no raise).
validator.validate("666-12-3456", TaxIdentifierType.SSN).valid   # False

# A wrong-length identifier raises.
try:
    validator.validate("123-45-67890", TaxIdentifierType.SSN)
except InvalidTaxIdError:
    ...  # 10 digits is not a valid SSN

# A type the country does not handle raises.
try:
    TaxValidator(Country.US).validate("X1", TaxIdentifierType.FOREIGN_TIN)
except UnsupportedTaxIdTypeError:
    ...  # US rules only handle US identifier types
```

Use `TaxValidationResult.from_tax_identifier` when you prefer a non-raising helper
that returns `None` for missing or malformed input:

```python
from tax_validation import TaxValidationResult, Country, TaxIdentifierType

summary = TaxValidationResult.from_tax_identifier(
    country=Country.US, tax_id="12-3456789", tax_id_type=TaxIdentifierType.EIN
)
summary.valid    # True
```

## Normalization utilities

The library provides normalization helpers and annotated Pydantic field types you
can reuse in your own models:

```python
from tax_validation import (
    clean_us_tax_identifier,
    format_us_ssn,
    format_us_ein,
    ComparableUsTaxIdentifier,
)

clean_us_tax_identifier(" 123-45-6789 ")            # "123456789"
format_us_ssn("123456789")                          # "123-45-6789"
format_us_ein("123456789")                          # "12-3456789"
ComparableUsTaxIdentifier("123-45-6789") == "123456789"   # True (ignores formatting)
```

```python
from tax_validation import BaseModel, NormalizedString, StringBool


def is_yes(value: str) -> bool:
    return value.strip().upper() in {"YES", "Y"}


class IntakeForm(BaseModel):
    business_name: NormalizedString(normalize_to_uppercase=True)
    consented: StringBool(predicate=is_yes)


form = IntakeForm(business_name="  acme llc ", consented="yes")
form.business_name    # "ACME LLC"
form.consented        # True
```

## Masking tax identifiers

Models that carry a `TaxIdField` can mask and unmask the value via the
`TaxIdentifierPairMixin`:

```python
from tax_validation import (
    BaseModel,
    Country,
    TaxIdentifierPairMixin,
    TaxIdentifierType,
    TaxIdField,
)


class ContractorTaxInfo(TaxIdentifierPairMixin, BaseModel):
    name: str
    tax_id: TaxIdField(country=Country.US, tax_id_type=TaxIdentifierType.SSN)


record = ContractorTaxInfo(name="Jane Doe", tax_id="123-45-6789")
record.tax_id == "123456789"                    # normalized on construction

masked = record.to_masked()
masked.tax_id                                    # "*******6789"
masked.to_unmask().tax_id == "123-45-6789"       # True
```

## Package layout

The top-level package holds country-agnostic scaffolding — `BaseModel`,
`BaseEnum`, the `Country` enum and `Country.from_string`, the `TaxIdentifierType` /
`TaxIdentifierOrigin` / `TinType` vocabulary, generic string normalization, the
`CountryTaxRules` strategy and `get_country_rules` registry, the generic
`TaxIdentifier`, `TaxValidationResult`, `TaxValidator`, and `TaxIdField`, and the
`GenericTaxRules` fallback. Country-specific code lives in its own subpackage
(`tax_validation.us`), which is also re-exported from the top level for convenience.

## Adding a country

`TaxValidator`, `TaxIdentifier`, `TaxIdField`, and `TaxValidationResult` are
generic and take a `Country`; they dispatch to a `CountryTaxRules` implementation
resolved by `get_country_rules`. Countries without a dedicated implementation fall
back to `GenericTaxRules`. To add first-class support for a country:

1. Implement `CountryTaxRules` (for example in `tax_validation/ca/rules.py`),
   defining `country`, `supported_types`, `normalize`, `is_valid`, and
   `resolve_metadata`.
2. Add a `match` arm to `get_country_rules` in `tax_validation/rules.py` that
   returns your rules for the new `Country` member.

No new models, fields, or validators are required.

## Development

```bash
poetry install --all-extras
poetry run pytest
```
