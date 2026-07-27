from functools import cached_property
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
from tax_identifiers.normalization import transform_required_string
from tax_identifiers.rules import get_country_rules

StrRequired = Annotated[str, "str_required", BeforeValidator(transform_required_string)]

TaxIdStr = Annotated[str, "tax_id"]


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

    @cached_property
    def maskable(self) -> "TaxIdFieldOptions":
        """Return the same options with already-masked input accepted."""

        return TaxIdFieldOptions(
            country=self.country,
            tax_id_type=self.tax_id_type,
            allow_masked=True,
        )

    def __get_pydantic_core_schema__(
        self, source_type: object, handler: GetCoreSchemaHandler
    ) -> core_schema.CoreSchema:
        """Wrap the validated string with country-aware tax ID normalization."""

        return core_schema.no_info_wrap_validator_function(self._normalize, handler(source_type))

    def _normalize(self, value: object, handler: ValidatorFunctionWrapHandler) -> str:
        """Normalize a tax ID value, accepting masked input only when allowed."""

        if isinstance(value, str) and (is_masked_tax_id(value) or contains_mask_characters(value)):
            if self.allow_masked:
                return MaskableTaxId(value, is_masked=True)

            raise ValueError(MASK_REJECTION_MESSAGE)

        return get_country_rules(self.country).normalize(handler(value), self.tax_id_type)


SSN_OPTIONS = TaxIdFieldOptions(country=Country.US, tax_id_type=TaxIdentifierType.SSN)

US_OPTIONS = TaxIdFieldOptions(country=Country.US)

FOREIGN_OPTIONS = TaxIdFieldOptions(tax_id_type=TaxIdentifierType.FOREIGN_TIN)

UNKNOWN_OPTIONS = TaxIdFieldOptions()

SSNTaxIdField = Annotated[TaxIdStr, SSN_OPTIONS]

USTaxIdField = Annotated[TaxIdStr, US_OPTIONS]

ForeignTaxIdField = Annotated[TaxIdStr, FOREIGN_OPTIONS]

UnknownTaxIdField = Annotated[TaxIdStr, UNKNOWN_OPTIONS]

MaskableUSTaxIdField = Annotated[TaxIdStr, US_OPTIONS.maskable]

MaskableForeignTaxIdField = Annotated[TaxIdStr, FOREIGN_OPTIONS.maskable]

MaskableUnknownTaxIdField = Annotated[TaxIdStr, UNKNOWN_OPTIONS.maskable]
