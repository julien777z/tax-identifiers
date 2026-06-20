from typing import Final

from tax_validation.countries import Country
from tax_validation.enums import TaxIdentifierType
from tax_validation.metadata import TaxIdentifierMetadata
from tax_validation.normalization import collapse_whitespace
from tax_validation.rules import CountryTaxRules

GENERIC_SUPPORTED_TYPES: Final[frozenset[TaxIdentifierType]] = frozenset(
    {TaxIdentifierType.FOREIGN_TIN, TaxIdentifierType.NONE}
)


class GenericTaxRules(CountryTaxRules):
    """Country-agnostic tax identifier rules for countries without dedicated logic."""

    def __init__(self, country: Country):
        """Store the country these generic rules report."""

        self._country = country

    @property
    def country(self) -> Country:
        """Return the country these rules handle."""

        return self._country

    @property
    def supported_types(self) -> frozenset[TaxIdentifierType]:
        """Return the country-agnostic tax identifier types."""

        return GENERIC_SUPPORTED_TYPES

    def normalize(self, tax_id: str, tax_id_type: TaxIdentifierType) -> str:
        """Return a whitespace-collapsed, uppercased tax identifier."""

        return collapse_whitespace(tax_id).upper()

    def is_valid(self, tax_id: str, tax_id_type: TaxIdentifierType) -> bool:
        """Raise; validity cannot be asserted without country-specific rules."""

        raise NotImplementedError(f"No tax identifier validation rules for {self._country}")

    def resolve_metadata(
        self, tax_id: str, tax_id_type: TaxIdentifierType
    ) -> TaxIdentifierMetadata | None:
        """Return None; generic rules resolve no country-specific metadata."""

        return None
