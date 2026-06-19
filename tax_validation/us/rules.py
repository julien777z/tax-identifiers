from tax_validation.countries import Country
from tax_validation.enums import TaxIdentifierOrigin, TaxIdentifierType
from tax_validation.metadata import TaxIdentifierMetadata
from tax_validation.rules import CountryTaxRules
from tax_validation.us.metadata import SSNValidation
from tax_validation.us.tax_identifiers import (
    US_TAX_IDENTIFIER_TYPES,
    ComparableUsTaxIdentifier,
    clean_us_tax_identifier,
    is_us_tax_identifier_type,
)
from tax_validation.us.transformers import transform_tax_identifier


class UsTaxRules(CountryTaxRules):
    """United States tax identifier rules (SSN, EIN, ITIN)."""

    @property
    def country(self) -> Country:
        """Return the country these rules handle."""

        return Country.US

    @property
    def supported_types(self) -> frozenset[TaxIdentifierType]:
        """Return the supported US tax identifier types."""

        return US_TAX_IDENTIFIER_TYPES

    def normalize(self, tax_id: str, tax_id_type: TaxIdentifierType) -> str:
        """Return a comparison-ready US tax identifier, raising on malformed input."""

        us_tin = is_us_tax_identifier_type(tax_id_type)
        origin = TaxIdentifierOrigin.US_TIN if us_tin else TaxIdentifierOrigin.FOREIGN_TIN
        normalized = transform_tax_identifier(tax_id, origin=origin)

        if normalized is None:
            raise ValueError("tax_id is required")

        if us_tin:
            return ComparableUsTaxIdentifier(tax_id)

        return normalized

    def is_valid(self, tax_id: str, tax_id_type: TaxIdentifierType) -> bool:
        """Return whether an SSN passes reserved-range checks; other US types are always valid."""

        if tax_id_type != TaxIdentifierType.SSN:
            return True

        try:
            cleaned = clean_us_tax_identifier(tax_id)
        except ValueError:
            return False

        if cleaned is None:
            return False

        area_number = cleaned[:3]
        group_number = cleaned[3:5]
        serial_number = cleaned[5:]

        return not (
            area_number in {"000", "666"}
            or int(area_number) >= 900
            or group_number == "00"
            or serial_number == "0000"
        )

    def resolve_metadata(
        self, tax_id: str, tax_id_type: TaxIdentifierType
    ) -> TaxIdentifierMetadata | None:
        """Return SSN allocation details when the identifier is an SSN."""

        if tax_id_type != TaxIdentifierType.SSN:
            return None

        return SSNValidation.from_tax_identifier(tax_id)
