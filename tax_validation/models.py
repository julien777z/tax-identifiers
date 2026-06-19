from functools import cached_property
from typing import Self

from pydantic import Field, SerializeAsAny, ValidationError, computed_field, model_validator

from tax_validation.base import BaseModel
from tax_validation.countries import Country
from tax_validation.enums import TaxIdentifierType
from tax_validation.metadata import TaxIdentifierMetadata
from tax_validation.rules import get_country_rules


class TaxIdentifier(BaseModel):
    """Normalized tax identifier with country-specific derived validation."""

    country: Country
    tax_id_type: TaxIdentifierType
    tax_id: str = Field(repr=False)

    @model_validator(mode="after")
    def normalize_tax_identifier(self) -> Self:
        """Normalize the tax identifier using its country's rules."""

        self.tax_id = get_country_rules(self.country).normalize(self.tax_id, self.tax_id_type)

        return self

    @computed_field
    @cached_property
    def metadata(self) -> SerializeAsAny[TaxIdentifierMetadata] | None:
        """Return resolved country-specific metadata when available."""

        return get_country_rules(self.country).resolve_metadata(str(self.tax_id), self.tax_id_type)

    @computed_field
    @property
    def valid(self) -> bool:
        """Return whether the identifier passes its country's structural checks."""

        return get_country_rules(self.country).is_valid(str(self.tax_id), self.tax_id_type)

    def __eq__(self, other: object) -> bool:
        """Check equality with another TaxIdentifier or a string."""

        if isinstance(other, TaxIdentifier):
            return (
                self.country == other.country
                and self.tax_id_type == other.tax_id_type
                and self.tax_id == other.tax_id
            )

        if isinstance(other, str):
            return self.tax_id == other

        return False

    def __hash__(self) -> int:
        """Hash by normalized tax ID to preserve model and string compatibility."""

        return hash(self.tax_id)


class TaxValidationResult(BaseModel):
    """Validation summary for a tax identifier without the raw value."""

    country: Country
    tax_id_type: TaxIdentifierType
    valid: bool
    metadata: SerializeAsAny[TaxIdentifierMetadata] | None = None

    @classmethod
    def from_tax_identifier(
        cls,
        *,
        country: Country,
        tax_id: str | None,
        tax_id_type: TaxIdentifierType | None,
    ) -> Self | None:
        """Build a validation summary from a raw identifier and type, or None when absent or malformed."""

        if tax_id is None or tax_id_type is None:
            return None

        try:
            identifier = TaxIdentifier(country=country, tax_id=tax_id, tax_id_type=tax_id_type)
        except (ValidationError, ValueError):
            return None

        return cls(
            country=identifier.country,
            tax_id_type=identifier.tax_id_type,
            valid=identifier.valid,
            metadata=identifier.metadata,
        )
