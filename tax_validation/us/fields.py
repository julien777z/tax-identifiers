from functools import partial
from typing import Annotated

from pydantic import AfterValidator, BeforeValidator

from tax_validation.enums import TaxIdentifierOrigin, TaxIdentifierType, TinType
from tax_validation.us.enums import USState
from tax_validation.us.tax_identifiers import (
    format_us_ein,
    strict_format_us_ssn,
    to_comparable_us_tax_identifier,
)
from tax_validation.us.transformers import transform_tax_id_field, transform_us_state


class TaxIdFieldOptions:
    """Annotation metadata for configuring tax ID field normalization."""

    def __init__(
        self,
        *,
        origin: TaxIdentifierOrigin,
        tin_type: TinType | None,
        allow_masked: bool = False,
    ):
        """Store tax ID field options for downstream validators."""

        self.origin = origin
        self.tin_type = tin_type
        self.allow_masked = allow_masked


def TaxIdField(  # pylint: disable=invalid-name
    *,
    origin: TaxIdentifierOrigin,
    tin_type: TinType | None = None,
    allow_masked: bool = False,
) -> object:
    """Return an annotated tax ID field with origin and tin-type-aware normalization."""

    return Annotated[
        str,
        "tax_id",
        TaxIdFieldOptions(
            origin=origin,
            tin_type=tin_type,
            allow_masked=allow_masked,
        ),
        AfterValidator(
            partial(
                transform_tax_id_field,
                origin=origin,
                tin_type=tin_type,
                allow_masked=allow_masked,
            )
        ),
    ]


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
