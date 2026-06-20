import pickle
from functools import cache
from pathlib import Path
from typing import Final, Self, TypedDict

from tax_identifiers.metadata import TaxIdentifierMetadata
from tax_identifiers.us.fields import USStateField
from tax_identifiers.us.tax_identifiers import clean_us_tax_identifier


class SSNAllocationEntry(TypedDict):
    """Issuing state and group-to-years mapping for an SSN area number."""

    state: str
    groups: dict[str, str]


STATIC_DIR: Final[Path] = Path(__file__).resolve().parent / "static"
SSN_ALLOCATION_FILE: Final[Path] = STATIC_DIR / "ssn_allocation.pkl"


@cache
def get_ssn_allocation_data() -> dict[str, SSNAllocationEntry]:
    """Load and cache the SSN allocation dataset on first use."""

    try:
        with SSN_ALLOCATION_FILE.open("rb") as allocation_file:
            payload = pickle.load(allocation_file)
    except FileNotFoundError as exc:
        raise RuntimeError(f"SSN allocation dataset file not found: {SSN_ALLOCATION_FILE}") from exc
    except pickle.UnpicklingError as exc:
        raise RuntimeError(f"SSN allocation dataset is not a valid pickle: {SSN_ALLOCATION_FILE}") from exc

    if not isinstance(payload, dict) or not payload:
        raise ValueError("SSN allocation dataset must be a non-empty mapping.")

    return payload


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
        allocation = get_ssn_allocation_data().get(area_number)

        if allocation is None:
            return None, None

        return allocation["state"], allocation["groups"].get(group_number)
