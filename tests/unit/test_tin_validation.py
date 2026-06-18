from collections.abc import Callable

import pytest

from tax_validation import TaxIdentifierType, TinValidation


class TestTinValidationFromTaxIdentifier:
    """Tests for building a validation summary from a raw identifier."""

    def test_summarizes_valid_ssn(self, tax_id_factory: Callable[..., str]) -> None:
        """Test that a valid SSN produces a summary with resolved details."""

        summary = TinValidation.from_tax_identifier(
            tax_id=tax_id_factory(TaxIdentifierType.SSN),
            tax_id_type=TaxIdentifierType.SSN,
        )

        assert summary is not None
        assert summary.tin_type == TaxIdentifierType.SSN
        assert summary.valid is True
        assert summary.ssn_validation is not None

    def test_summarizes_reserved_ssn_as_invalid(self) -> None:
        """Test that a structurally reserved SSN is summarized as invalid."""

        summary = TinValidation.from_tax_identifier(
            tax_id="666-12-3456",
            tax_id_type=TaxIdentifierType.SSN,
        )

        assert summary is not None
        assert summary.valid is False

    def test_returns_none_for_malformed_identifier(self) -> None:
        """Test that an identifier without nine digits resolves to None."""

        summary = TinValidation.from_tax_identifier(
            tax_id="123",
            tax_id_type=TaxIdentifierType.SSN,
        )

        assert summary is None

    @pytest.mark.parametrize(
        ("provide_id", "provide_type"),
        [(False, True), (True, False)],
        ids=["missing_id", "missing_type"],
    )
    def test_returns_none_when_inputs_absent(
        self,
        tax_id_factory: Callable[..., str],
        provide_id: bool,
        provide_type: bool,
    ) -> None:
        """Test that a missing identifier or type resolves to None."""

        summary = TinValidation.from_tax_identifier(
            tax_id=tax_id_factory(TaxIdentifierType.SSN) if provide_id else None,
            tax_id_type=TaxIdentifierType.SSN if provide_type else None,
        )

        assert summary is None
