from collections.abc import Callable

import pytest

from tax_validation import (
    Country,
    InvalidTaxIdError,
    TaxIdentifierType,
    USState,
    USTaxValidator,
    UnsupportedTaxIdTypeError,
)


class TestUSTaxValidatorCountry:
    """Tests for the validator's country identity."""

    def test_reports_united_states(self, us_validator: USTaxValidator) -> None:
        """Test that the US validator reports the United States."""

        assert us_validator.country == Country.US


class TestUSTaxValidatorValidate:
    """Tests for validating US tax identifiers."""

    def test_returns_resolution_for_valid_ssn(
        self,
        us_validator: USTaxValidator,
        tax_id_factory: Callable[..., str],
    ) -> None:
        """Test that a valid SSN returns a summary with resolved details."""

        result = us_validator.validate(tax_id_factory(TaxIdentifierType.SSN), TaxIdentifierType.SSN)

        assert result.valid is True
        assert result.ssn_validation is not None

    @pytest.mark.parametrize(
        "tax_id",
        ["123-45-67890", "12345"],
        ids=["too_long", "too_short"],
    )
    def test_rejects_structurally_invalid_ssn(
        self,
        us_validator: USTaxValidator,
        tax_id: str,
    ) -> None:
        """Test that an SSN without nine digits is rejected."""

        with pytest.raises(InvalidTaxIdError):
            us_validator.validate(tax_id, TaxIdentifierType.SSN)

    @pytest.mark.parametrize(
        "tax_id_type",
        [TaxIdentifierType.FOREIGN_TIN, TaxIdentifierType.NONE],
        ids=["foreign", "none"],
    )
    def test_rejects_unsupported_types(
        self,
        us_validator: USTaxValidator,
        tax_id_factory: Callable[..., str],
        tax_id_type: TaxIdentifierType,
    ) -> None:
        """Test that a non-US identifier type is rejected."""

        with pytest.raises(UnsupportedTaxIdTypeError):
            us_validator.validate(tax_id_factory(TaxIdentifierType.SSN), tax_id_type)


class TestUSTaxValidatorResolveSsn:
    """Tests for the SSN resolution helper."""

    def test_resolves_known_ssn(
        self,
        us_validator: USTaxValidator,
        ssn_allocation: dict[str, dict[str, object]],
    ) -> None:
        """Test that a known SSN resolves to issuing details."""

        area, entry = next(iter(ssn_allocation.items()))
        groups = entry["groups"]
        assert isinstance(groups, dict)
        group = next(iter(groups))

        validation = us_validator.resolve_ssn(f"{area}{group}0001")

        assert validation is not None
        assert validation.issued_state == USState(entry["state"])

    def test_returns_none_for_invalid_ssn(self, us_validator: USTaxValidator) -> None:
        """Test that an SSN without nine digits resolves to None."""

        assert us_validator.resolve_ssn("12345") is None
