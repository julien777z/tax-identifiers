from abc import ABC, abstractmethod
from functools import cache

from tax_identifiers.countries import Country
from tax_identifiers.enums import TaxIdentifierType
from tax_identifiers.metadata import TaxIdentifierMetadata


class CountryTaxRules(ABC):
    """Country-specific normalization and validation rules for tax identifiers."""

    @property
    @abstractmethod
    def country(self) -> Country:
        """Return the country these rules handle."""

    @property
    @abstractmethod
    def supported_types(self) -> frozenset[TaxIdentifierType]:
        """Return the tax identifier types these rules validate."""

    @abstractmethod
    def normalize(self, tax_id: str, tax_id_type: TaxIdentifierType) -> str:
        """Return the canonical, comparison-ready form of a tax identifier."""

    @abstractmethod
    def is_valid(self, tax_id: str, tax_id_type: TaxIdentifierType) -> bool:
        """Return whether a normalized tax identifier passes structural checks."""

    @abstractmethod
    def resolve_metadata(
        self, tax_id: str, tax_id_type: TaxIdentifierType
    ) -> TaxIdentifierMetadata | None:
        """Return resolved metadata for a tax identifier, or None when unavailable."""


@cache
def get_country_rules(country: Country) -> CountryTaxRules:
    """Return the tax rules for a country, falling back to generic rules."""

    match country:
        case Country.US:
            from tax_identifiers.us.rules import UsTaxRules

            return UsTaxRules()
        case _:
            from tax_identifiers.generic import GenericTaxRules

            return GenericTaxRules(country)
