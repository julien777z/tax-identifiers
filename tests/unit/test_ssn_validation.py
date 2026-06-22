import json
from collections.abc import Callable

import pytest

from tax_identifiers import SSNValidation
from tax_identifiers.us.metadata import STATIC_DIR, SSNAllocationEntry, get_ssn_allocation_data
from tests.conftest import AllocatedSsn


class TestSSNValidationFromTaxIdentifier:
    """Tests for resolving SSN allocation details."""

    def test_resolves_known_area_and_group(
        self,
        allocated_ssn_factory: Callable[..., AllocatedSsn],
    ) -> None:
        """Test that a known area and group resolve to issuing state and years."""

        allocated = allocated_ssn_factory()
        validation = SSNValidation.from_tax_identifier(allocated.tax_id)

        assert validation is not None
        assert validation.issued_state == allocated.issued_state
        assert validation.issued_years == allocated.issued_years

    def test_unknown_area_resolves_without_state(
        self,
        ssn_allocation: dict[str, SSNAllocationEntry],
    ) -> None:
        """Test that an unallocated area resolves to a validation without a state."""

        unknown_area = "543"
        assert unknown_area not in ssn_allocation

        validation = SSNValidation.from_tax_identifier(f"{unknown_area}010001")

        assert validation is not None
        assert validation.issued_state is None
        assert validation.issued_years is None

    @pytest.mark.parametrize("tax_id", ["12345", "abcdefghij"], ids=["too_short", "non_numeric"])
    def test_returns_none_for_invalid_identifier(self, tax_id: str) -> None:
        """Test that an identifier without nine digits resolves to None."""

        assert SSNValidation.from_tax_identifier(tax_id) is None


class TestSSNAllocationDataset:
    """Tests for the shipped SSN allocation dataset."""

    def test_pickle_matches_json_source(self) -> None:
        """Test that the loaded pickle matches the JSON source of truth."""

        with (STATIC_DIR / "ssn_allocation.json").open(encoding="utf-8") as source_file:
            json_data = json.load(source_file)

        assert get_ssn_allocation_data() == json_data
