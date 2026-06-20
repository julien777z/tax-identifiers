from collections.abc import Callable
from functools import partial
from typing import Annotated

from pydantic import AfterValidator, BeforeValidator

from tax_identifiers.countries import Country
from tax_identifiers.enums import TaxIdentifierType
from tax_identifiers.normalization import build_string_normalizer, transform_required_string
from tax_identifiers.rules import get_country_rules


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


StrRequired = Annotated[str, "str_required", BeforeValidator(transform_required_string)]


class TaxIdFieldOptions:
    """Annotation metadata for configuring tax ID field normalization."""

    def __init__(
        self,
        *,
        country: Country,
        tax_id_type: TaxIdentifierType,
        allow_masked: bool = False,
    ):
        """Store tax ID field options for downstream validators."""

        self.country = country
        self.tax_id_type = tax_id_type
        self.allow_masked = allow_masked


def normalize_tax_id_field(
    value: str,
    *,
    country: Country,
    tax_id_type: TaxIdentifierType,
    allow_masked: bool,
) -> str:
    """Normalize a tax ID field value via its country's rules, optionally allowing masked input."""

    if "*" in value:
        if allow_masked:
            return value

        raise ValueError("Tax ID cannot contain mask characters")

    return get_country_rules(country).normalize(value, tax_id_type)


def TaxIdField(  # pylint: disable=invalid-name
    *,
    country: Country = Country.UNKNOWN,
    tax_id_type: TaxIdentifierType = TaxIdentifierType.US_UNSPECIFIED,
    allow_masked: bool = False,
) -> object:
    """Return an annotated tax ID field with country-aware normalization."""

    return Annotated[
        str,
        "tax_id",
        TaxIdFieldOptions(
            country=country,
            tax_id_type=tax_id_type,
            allow_masked=allow_masked,
        ),
        AfterValidator(
            partial(
                normalize_tax_id_field,
                country=country,
                tax_id_type=tax_id_type,
                allow_masked=allow_masked,
            )
        ),
    ]

