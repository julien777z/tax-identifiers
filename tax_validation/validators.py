from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from tax_validation.base import BaseModel
from tax_validation.enums import Country, TaxIdentifierType

ValidationResultT = TypeVar("ValidationResultT", bound=BaseModel)


class TaxValidator(ABC, Generic[ValidationResultT]):
    """Abstract base for country-specific tax identifier validators."""

    @property
    @abstractmethod
    def country(self) -> Country:
        """Return the country this validator handles."""

    @abstractmethod
    def validate(self, tax_id: str, tax_id_type: TaxIdentifierType) -> ValidationResultT:
        """Validate a tax identifier and return its resolved validation summary."""
