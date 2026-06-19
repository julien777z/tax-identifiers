import json
from pathlib import Path
from typing import Final, Self, TypedDict

from tax_validation.metadata import TaxIdentifierMetadata
from tax_validation.us.fields import USStateField
from tax_validation.us.tax_identifiers import clean_us_tax_identifier


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


class SSNValidation(TaxIdentifierMetadata):
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


initialize_dataset()
