from abc import ABC, abstractmethod

from tax_validation.enums import Country, TaxIdentifierType
from tax_validation.models.tin import TinValidation


class TaxValidator(ABC):
    """Abstract base for country-specific tax identifier validators."""

    @property
    @abstractmethod
    def country(self) -> Country:
        """Return the country this validator handles."""

    @abstractmethod
    def validate(self, tax_id: str, tax_id_type: TaxIdentifierType) -> TinValidation:
        """Validate a tax identifier and return its resolved validation summary."""
