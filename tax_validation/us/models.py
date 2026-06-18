import json
from functools import cached_property
from pathlib import Path
from typing import Final, Self, TypedDict

from pydantic import Field, ValidationError, computed_field, model_validator

from tax_validation.base import BaseModel
from tax_validation.enums import TaxIdentifierOrigin, TaxIdentifierType
from tax_validation.us.fields import USStateField
from tax_validation.us.tax_identifiers import (
    ComparableUsTaxIdentifier,
    clean_us_tax_identifier,
    is_us_tax_identifier_type,
)
from tax_validation.us.transformers import transform_tax_identifier


class SSNAllocationEntry(TypedDict):
    """Issuing state and group-to-years mapping for an SSN area number."""

    state: str
    groups: dict[str, str]


STATIC_DIR: Final[Path] = Path(__file__).resolve().parent / "static"
SSN_ALLOCATION_FILE: Final[Path] = STATIC_DIR / "ssn_allocation.json"
SSN_ALLOCATION_DATA: Final[dict[str, SSNAllocationEntry]] = {}


def initialize_dataset() -> None:
    """Load the SSN allocation dataset into memory once."""

    if SSN_ALLOCATION_DATA:
        return

    try:
        with SSN_ALLOCATION_FILE.open(encoding="utf-8") as allocation_file:
            payload = json.load(allocation_file)
    except FileNotFoundError as exc:
        raise RuntimeError(f"SSN allocation dataset file not found: {SSN_ALLOCATION_FILE}") from exc
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"SSN allocation dataset is not valid JSON: {SSN_ALLOCATION_FILE}") from exc

    if not isinstance(payload, dict) or not payload:
        raise ValueError("SSN allocation dataset must be a non-empty mapping.")

    SSN_ALLOCATION_DATA.update(payload)


class SSNValidation(BaseModel):
    """SSN validation details derived from a tax identifier."""

    issued_state: USStateField | None = None
    issued_years: str | None = None

    @classmethod
    def from_tax_identifier(cls, tax_identifier: str) -> Self | None:
        """Return SSN allocation details for a tax identifier, or None when invalid."""

        try:
            normalized = clean_us_tax_identifier(tax_identifier)
        except ValueError:
            return None

        if not normalized:
            return None

        issued_state, issued_years = cls.lookup_allocation(normalized)

        return cls(issued_state=issued_state, issued_years=issued_years)

    @staticmethod
    def lookup_allocation(normalized: str) -> tuple[str | None, str | None]:
        """Look up issuing state and issued years from the SSN allocation dataset."""

        area_number = normalized[:3]
        group_number = normalized[3:5]
        allocation = SSN_ALLOCATION_DATA.get(area_number)

        if allocation is None:
            return None, None

        return allocation["state"], allocation["groups"].get(group_number)


class TaxIdentifierModel(BaseModel):
    """Normalized tax identifier model with derived validation helpers."""

    tax_id_type: TaxIdentifierType
    tax_id: str = Field(repr=False)

    @model_validator(mode="after")
    def normalize_tax_identifier(self) -> Self:
        """Normalize the tax identifier using the explicit tax identifier type."""

        raw_tax_identifier = self.tax_id
        origin = TaxIdentifierOrigin.US_TIN if self.us_tin else TaxIdentifierOrigin.FOREIGN_TIN
        normalized_tax_identifier = transform_tax_identifier(raw_tax_identifier, origin=origin)

        if normalized_tax_identifier is None:
            raise ValueError("tax_id is required")

        if self.us_tin:
            self.tax_id = ComparableUsTaxIdentifier(raw_tax_identifier)
        else:
            self.tax_id = normalized_tax_identifier

        return self

    @property
    def us_tin(self) -> bool:
        """Return whether the identifier type is a US tax identifier."""

        return is_us_tax_identifier_type(self.tax_id_type)

    @computed_field
    @cached_property
    def ssn_validation(self) -> SSNValidation | None:
        """Return SSN validation details when the identifier is an SSN."""

        if self.tax_id_type != TaxIdentifierType.SSN:
            return None

        return SSNValidation.from_tax_identifier(str(self.tax_id))

    @computed_field
    @property
    def valid(self) -> bool:
        """Return whether the TIN passes reserved SSN checks."""

        if self.tax_id_type != TaxIdentifierType.SSN:
            return True

        try:
            tax_identifier = clean_us_tax_identifier(str(self.tax_id))
        except ValueError:
            return False

        if tax_identifier is None:
            return False

        area_number = tax_identifier[:3]
        group_number = tax_identifier[3:5]
        serial_number = tax_identifier[5:]

        return not (
            area_number in {"000", "666"}
            or int(area_number) >= 900
            or group_number == "00"
            or serial_number == "0000"
        )

    def __eq__(self, other: object) -> bool:
        """Check equality with another TaxIdentifierModel or a string."""

        if not isinstance(other, (TaxIdentifierModel, str)):
            return False

        if isinstance(other, TaxIdentifierModel):
            return self.tax_id_type == other.tax_id_type and self.tax_id == other.tax_id

        if self.us_tin:
            try:
                cleaned_other = clean_us_tax_identifier(other)
            except ValueError:
                return False

            return self.tax_id == cleaned_other

        return str(self.tax_id) == str(other)

    def __hash__(self) -> int:
        """Hash by normalized tax ID to preserve model and string compatibility."""

        return hash(self.tax_id)


class TinValidation(BaseModel):
    """Validation summary for a tax identifier without the raw value."""

    tin_type: TaxIdentifierType
    ssn_validation: SSNValidation | None = None
    valid: bool

    @classmethod
    def from_tax_identifier(
        cls,
        *,
        tax_id: str | None,
        tax_id_type: TaxIdentifierType | None,
    ) -> Self | None:
        """Build a validation summary from a raw identifier and type, or None when absent or malformed."""

        if tax_id is None or tax_id_type is None:
            return None

        try:
            model = TaxIdentifierModel(tax_id=tax_id, tax_id_type=tax_id_type)
        except (ValidationError, ValueError):
            return None

        return cls(
            tin_type=model.tax_id_type,
            ssn_validation=model.ssn_validation,
            valid=model.valid,
        )


initialize_dataset()
