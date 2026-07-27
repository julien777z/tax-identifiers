from collections.abc import Callable
from typing import Annotated

from pydantic import BeforeValidator, GetCoreSchemaHandler, ValidatorFunctionWrapHandler
from pydantic_core import core_schema

from tax_identifiers.countries import Country
from tax_identifiers.enums import TaxIdentifierType
from tax_identifiers.masking import (
    MASK_REJECTION_MESSAGE,
    MaskableTaxId,
    contains_mask_characters,
    is_masked_tax_id,
)
from tax_identifiers.normalization import build_string_normalizer, transform_required_string
from tax_identifiers.rules import get_country_rules

StrRequired = Annotated[str, "str_required", BeforeValidator(transform_required_string)]


class NormalizedStringOptions:
    """Annotation metadata applying configurable normalization to a string field."""

    def __init__(
        self,
        *,
        normalize_to_uppercase: bool = False,
        normalize_to_lowercase: bool = False,
        normalize_to_titlecase: bool = False,
        strip_non_digits: bool = False,
        strip_trailing_punctuation: bool = False,
    ):
        """Build the normalizer for these options, rejecting conflicting casing flags."""

        self.normalize_to_uppercase = normalize_to_uppercase
        self.normalize_to_lowercase = normalize_to_lowercase
        self.normalize_to_titlecase = normalize_to_titlecase
        self.strip_non_digits = strip_non_digits
        self.strip_trailing_punctuation = strip_trailing_punctuation
        self.normalizer = build_string_normalizer(
            normalize_to_uppercase=normalize_to_uppercase,
            normalize_to_lowercase=normalize_to_lowercase,
            normalize_to_titlecase=normalize_to_titlecase,
            strip_non_digits=strip_non_digits,
            strip_trailing_punctuation=strip_trailing_punctuation,
        )

    def __get_pydantic_core_schema__(
        self, source_type: object, handler: GetCoreSchemaHandler
    ) -> core_schema.CoreSchema:
        """Normalize the validated string using this annotation's options."""

        return core_schema.no_info_after_validator_function(self.normalizer, handler(source_type))


class StringBoolOptions:
    """Annotation metadata converting string input to a bool via a caller-supplied predicate."""

    def __init__(self, *, predicate: Callable[[str], bool]):
        """Store the predicate used to interpret string input."""

        self.predicate = predicate

    def __get_pydantic_core_schema__(
        self, source_type: object, handler: GetCoreSchemaHandler
    ) -> core_schema.CoreSchema:
        """Convert string input through the predicate before bool validation."""

        return core_schema.no_info_before_validator_function(self._transform, handler(source_type))

    def _transform(self, value: bool | str) -> bool:
        """Return the value unchanged when already a bool, otherwise apply the predicate."""

        if isinstance(value, bool):
            return value

        return self.predicate(str(value))


def normalize_tax_id_field(
    value: object,
    handler: ValidatorFunctionWrapHandler,
    *,
    country: Country,
    tax_id_type: TaxIdentifierType,
    allow_masked: bool,
) -> str:
    """Normalize a tax ID field value, accepting masked values only when allowed."""

    if isinstance(value, str) and (is_masked_tax_id(value) or contains_mask_characters(value)):
        if allow_masked:
            return MaskableTaxId(value, is_masked=True)

        raise ValueError(MASK_REJECTION_MESSAGE)

    return get_country_rules(country).normalize(handler(value), tax_id_type)


class TaxIdFieldOptions:
    """Annotation metadata for configuring tax ID field normalization."""

    def __init__(
        self,
        *,
        country: Country = Country.UNKNOWN,
        tax_id_type: TaxIdentifierType = TaxIdentifierType.US_UNSPECIFIED,
        allow_masked: bool = False,
    ):
        """Store tax ID field options for downstream validators."""

        self.country = country
        self.tax_id_type = tax_id_type
        self.allow_masked = allow_masked

    def __get_pydantic_core_schema__(
        self, source_type: object, handler: GetCoreSchemaHandler
    ) -> core_schema.CoreSchema:
        """Wrap the validated string with country-aware tax ID normalization."""

        return core_schema.no_info_wrap_validator_function(self._normalize, handler(source_type))

    def _normalize(self, value: object, handler: ValidatorFunctionWrapHandler) -> str:
        """Normalize a tax ID value using this annotation's country and type."""

        return normalize_tax_id_field(
            value,
            handler,
            country=self.country,
            tax_id_type=self.tax_id_type,
            allow_masked=self.allow_masked,
        )


UppercaseString = Annotated[
    str, "normalized_string", NormalizedStringOptions(normalize_to_uppercase=True)
]

LowercaseString = Annotated[
    str, "normalized_string", NormalizedStringOptions(normalize_to_lowercase=True)
]

TitlecaseString = Annotated[
    str, "normalized_string", NormalizedStringOptions(normalize_to_titlecase=True)
]

DigitsOnlyString = Annotated[
    str, "normalized_string", NormalizedStringOptions(strip_non_digits=True)
]

SSNTaxIdField = Annotated[
    str,
    "tax_id",
    TaxIdFieldOptions(country=Country.US, tax_id_type=TaxIdentifierType.SSN),
]

EINTaxIdField = Annotated[
    str,
    "tax_id",
    TaxIdFieldOptions(country=Country.US, tax_id_type=TaxIdentifierType.EIN),
]

ITINTaxIdField = Annotated[
    str,
    "tax_id",
    TaxIdFieldOptions(country=Country.US, tax_id_type=TaxIdentifierType.ITIN),
]

USTaxIdField = Annotated[
    str,
    "tax_id",
    TaxIdFieldOptions(country=Country.US, tax_id_type=TaxIdentifierType.US_UNSPECIFIED),
]

ForeignTaxIdField = Annotated[
    str,
    "tax_id",
    TaxIdFieldOptions(country=Country.UNKNOWN, tax_id_type=TaxIdentifierType.FOREIGN_TIN),
]

UnknownTaxIdField = Annotated[
    str,
    "tax_id",
    TaxIdFieldOptions(country=Country.UNKNOWN, tax_id_type=TaxIdentifierType.US_UNSPECIFIED),
]

MaskableSSNTaxIdField = Annotated[
    str,
    "tax_id",
    TaxIdFieldOptions(country=Country.US, tax_id_type=TaxIdentifierType.SSN, allow_masked=True),
]

MaskableEINTaxIdField = Annotated[
    str,
    "tax_id",
    TaxIdFieldOptions(country=Country.US, tax_id_type=TaxIdentifierType.EIN, allow_masked=True),
]

MaskableITINTaxIdField = Annotated[
    str,
    "tax_id",
    TaxIdFieldOptions(country=Country.US, tax_id_type=TaxIdentifierType.ITIN, allow_masked=True),
]

MaskableUSTaxIdField = Annotated[
    str,
    "tax_id",
    TaxIdFieldOptions(
        country=Country.US,
        tax_id_type=TaxIdentifierType.US_UNSPECIFIED,
        allow_masked=True,
    ),
]

MaskableForeignTaxIdField = Annotated[
    str,
    "tax_id",
    TaxIdFieldOptions(
        country=Country.UNKNOWN,
        tax_id_type=TaxIdentifierType.FOREIGN_TIN,
        allow_masked=True,
    ),
]

MaskableUnknownTaxIdField = Annotated[
    str,
    "tax_id",
    TaxIdFieldOptions(
        country=Country.UNKNOWN,
        tax_id_type=TaxIdentifierType.US_UNSPECIFIED,
        allow_masked=True,
    ),
]
