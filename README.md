# tax-validation

Validate tax identifiers and resolve their metadata with Pydantic. The library
rejects tax IDs that do not conform to their country's structural rules (currently
only US tax identifiers are supported) and returns resolved details such as an
SSN's issuing state and issued years.

## Installation

```bash
pip install tax-validation
```

## Quick start

```python
from tax_validation import USTaxValidator, TaxIdentifierType

validator = USTaxValidator()

result = validator.validate("123-45-6789", TaxIdentifierType.SSN)
result.valid                        # True (passes reserved-range checks)
result.tin_type                     # TaxIdentifierType.SSN
result.ssn_validation.issued_state  # a USState enum (serializes to e.g. "NY")
result.ssn_validation.issued_years  # e.g. "1936-1950"
```

`validate` raises when the identifier is structurally malformed or its type is
unsupported; otherwise it returns a `TinValidation` summary whose `valid` flag
reflects the reserved-range checks:

```python
from tax_validation import InvalidTaxIdError, UnsupportedTaxIdTypeError

# A parseable SSN returns a summary; reserved ranges set valid=False (no raise).
result = validator.validate("666-12-3456", TaxIdentifierType.SSN)
result.valid   # False (666 is a reserved area)

# A wrong-length identifier raises.
try:
    validator.validate("123-45-67890", TaxIdentifierType.SSN)
except InvalidTaxIdError:
    ...  # 10 digits is not a valid SSN

# An unsupported type raises.
try:
    validator.validate("X1", TaxIdentifierType.FOREIGN_TIN)
except UnsupportedTaxIdTypeError:
    ...  # USTaxValidator only handles US identifier types
```

Use `TinValidation.from_tax_identifier` when you prefer a non-raising helper that
returns `None` for missing or malformed input:

```python
from tax_validation import TinValidation, TaxIdentifierType

summary = TinValidation.from_tax_identifier(tax_id="12-3456789", tax_id_type=TaxIdentifierType.EIN)
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
    TaxIdentifierPairMixin,
    TaxIdField,
    TaxIdentifierOrigin,
    TinType,
)


class ContractorTaxInfo(TaxIdentifierPairMixin, BaseModel):
    name: str
    tax_id: TaxIdField(origin=TaxIdentifierOrigin.US_TIN, tin_type=TinType.SSN)


record = ContractorTaxInfo(name="Jane Doe", tax_id="123-45-6789")
record.tax_id == "123456789"                    # normalized on construction

masked = record.to_masked()
masked.tax_id                                    # "*******6789"
masked.to_unmask().tax_id == "123-45-6789"       # True
```

## Package layout

The top-level package holds country-agnostic scaffolding — `BaseModel`,
`BaseEnum`, `Country`, the `TaxIdentifierType` / `TaxIdentifierOrigin` / `TinType`
vocabulary, generic string normalization, and the `TaxValidator` abstract base.
Country-specific code lives in its own subpackage (`tax_validation.us`), which is
also re-exported from the top level for convenience.

## Adding a country

`TaxValidator` is the shared, generic abstract base
(`TaxValidator[ValidationResultT]`). A new country adds a `Country` member, a
subpackage (for example `tax_validation/ca/`), and a `TaxValidator` subclass that
implements `validate` and a `country` property. Country-specific validators are
free to add their own helpers (for example, `USTaxValidator.resolve_ssn`).

## Development

```bash
poetry install --all-extras
poetry run pytest
```
