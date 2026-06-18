from collections.abc import Callable
from functools import partial
from typing import Annotated

from pydantic import AfterValidator, BeforeValidator

from tax_validation.enums import TaxIdentifierOrigin, TaxIdentifierType, TinType, USState
from tax_validation.normalization.tax_identifiers import (
    format_us_ein,
    strict_format_us_ssn,
    to_comparable_us_tax_identifier,
)
from tax_validation.normalization.transformers import (
    build_string_normalizer,
    transform_required_string,
    transform_tax_id_field,
    transform_us_state,
)


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


def NormalizedString(  # pylint: disable=invalid-name
    label: str = "normalized_string",
    *,
    normalize_to_uppercase: bool = False,
    normalize_to_lowercase: bool = False,
    normalize_to_titlecase: bool = False,
    strip_non_digits: bool = False,
    strip_trailing_punctuation: bool = False,
) -> object:
    """Return an annotated string type with configurable normalization steps."""

    normalizer = build_string_normalizer(
        normalize_to_uppercase=normalize_to_uppercase,
        normalize_to_lowercase=normalize_to_lowercase,
        normalize_to_titlecase=normalize_to_titlecase,
        strip_non_digits=strip_non_digits,
        strip_trailing_punctuation=strip_trailing_punctuation,
    )

    return Annotated[str, label, AfterValidator(normalizer)]


def StringBool(  # pylint: disable=invalid-name
    *,
    predicate: Callable[[str], bool],
    label: str = "string_bool",
) -> object:
    """Return an annotated bool field that converts strings via a caller-supplied predicate."""

    def _transform(value: bool | str) -> bool:
        if isinstance(value, bool):
            return value

        return predicate(str(value))

    return Annotated[bool, label, BeforeValidator(_transform)]


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

StrRequired = Annotated[str, "str_required", BeforeValidator(transform_required_string)]

USStateField = Annotated[USState, "us_state", BeforeValidator(transform_us_state)]
