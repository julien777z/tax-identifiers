from pydantic import GetCoreSchemaHandler, ValidatorFunctionWrapHandler
from pydantic_core import core_schema

from tax_identifiers.countries import Country
from tax_identifiers.enums import TaxIdentifierType
from tax_identifiers.exceptions import InvalidTaxIdError
from tax_identifiers.masking import (
    MASK_REJECTION_MESSAGE,
    MaskableTaxId,
    contains_mask_characters,
    is_masked_tax_id,
)
from tax_identifiers.rules import get_country_rules


class TaxIdFieldOptions:
    """Annotation metadata for configuring tax ID field normalization."""

    def __init__(
        self,
        *,
        country: Country = Country.UNKNOWN,
        tax_id_type: TaxIdentifierType = TaxIdentifierType.US_UNSPECIFIED,
        allow_masked: bool = False,
        assert_validity: bool = True,
    ):
        """Store tax ID field options for downstream validators."""

        self.country = country
        self.tax_id_type = tax_id_type
        self.allow_masked = allow_masked
        self.assert_validity = assert_validity

    def __get_pydantic_core_schema__(
        self, source_type: object, handler: GetCoreSchemaHandler
    ) -> core_schema.CoreSchema:
        """Wrap the validated string with country-aware tax ID normalization."""

        return core_schema.no_info_wrap_validator_function(self.normalize, handler(source_type))

    def normalize(self, value: object, handler: ValidatorFunctionWrapHandler) -> str:
        """Normalize a tax ID value and reject it when its country's rules find it invalid."""

        if isinstance(value, str) and (is_masked_tax_id(value) or contains_mask_characters(value)):
            if self.allow_masked:
                return MaskableTaxId(value, is_masked=True)

            raise ValueError(MASK_REJECTION_MESSAGE)

        rules = get_country_rules(self.country)
        normalized = rules.normalize(handler(value), self.tax_id_type)

        if (
            self.assert_validity
            and rules.can_assert_validity
            and not rules.is_valid(normalized, self.tax_id_type)
        ):
            raise InvalidTaxIdError(
                f"{self.tax_id_type} value is not a valid {self.country} tax identifier"
            )

        return normalized
