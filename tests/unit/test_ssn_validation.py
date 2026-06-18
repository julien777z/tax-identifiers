import pytest

from tax_validation import SSNValidation, USState
from tax_validation.us.models import SSNAllocationEntry


class TestSSNValidationFromTaxIdentifier:
    """Tests for resolving SSN allocation details."""

    def test_resolves_known_area_and_group(
        self,
        ssn_allocation: dict[str, SSNAllocationEntry],
    ) -> None:
        """Test that a known area and group resolve to issuing state and years."""

        area, entry = next(iter(ssn_allocation.items()))
        group, years = next(iter(entry["groups"].items()))

        validation = SSNValidation.from_tax_identifier(f"{area}{group}0001")

        assert validation is not None
        assert validation.issued_state == USState(entry["state"])
        assert validation.issued_years == years

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
