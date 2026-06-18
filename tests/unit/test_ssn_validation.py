import pytest

from tax_validation import SSNValidation, USState


class TestSSNValidationFromTaxIdentifier:
    """Tests for resolving SSN allocation details."""

    def test_resolves_known_area_and_group(self) -> None:
        """Test that a known area and group resolve to issuing state and years."""

        validation = SSNValidation.from_tax_identifier("001-01-0001")

        assert validation is not None
        assert validation.issued_state == USState.NEW_HAMPSHIRE
        assert validation.issued_years == "1936-1950"

    def test_unknown_area_resolves_without_state(self) -> None:
        """Test that an unallocated area resolves to a validation without a state."""

        validation = SSNValidation.from_tax_identifier("999-99-9999")

        assert validation is not None
        assert validation.issued_state is None

    @pytest.mark.parametrize("tax_id", ["12345", "abcdefghij"], ids=["too_short", "non_numeric"])
    def test_returns_none_for_invalid_identifier(self, tax_id: str) -> None:
        """Test that an identifier without nine digits resolves to None."""

        assert SSNValidation.from_tax_identifier(tax_id) is None
