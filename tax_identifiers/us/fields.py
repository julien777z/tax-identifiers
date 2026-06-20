from typing import Annotated

from pydantic import AfterValidator, BeforeValidator

from tax_identifiers.enums import TaxIdentifierType
from tax_identifiers.us.enums import USState
from tax_identifiers.us.tax_identifiers import (
    format_us_ein,
    strict_format_us_ssn,
    to_comparable_us_tax_identifier,
)
from tax_identifiers.us.transformers import transform_us_state

TaxIdentifierTypeField = Annotated[TaxIdentifierType, "tax_id_type"]

EINFormattedField = Annotated[
    str,
    "ein",
    BeforeValidator(format_us_ein),
    AfterValidator(to_comparable_us_tax_identifier),
]

SSNFormattedField = Annotated[
    str,
    "ssn_formatted",
    BeforeValidator(strict_format_us_ssn),
    AfterValidator(to_comparable_us_tax_identifier),
]

USStateField = Annotated[USState, "us_state", BeforeValidator(transform_us_state)]
