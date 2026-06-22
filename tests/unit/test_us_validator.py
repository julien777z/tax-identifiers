from collections.abc import Callable

import pytest

from tax_identifiers import (
    Country,
    InvalidTaxIdError,
    SSNValidation,
    TaxIdentifierType,
    TaxValidator,
    UnsupportedTaxIdTypeError,
    UsTaxRules,
)
from tests.conftest import AllocatedSsn


class TestUsTaxValidatorCountry:
    """Tests for the validator's country identity."""

    def test_reports_united_states(self, us_validator: TaxValidator) -> None:
        """Test that the US validator reports the United States."""

        assert us_validator.country == Country.US


class TestUsTaxValidatorValidate:
    """Tests for validating US tax identifiers."""

    def test_returns_resolution_for_valid_ssn(
        self,
        us_validator: TaxValidator,
        tax_id_factory: Callable[..., str],
    ) -> None:
        """Test that a valid SSN returns a summary with resolved details."""

        result = us_validator.validate(tax_id_factory(TaxIdentifierType.SSN), TaxIdentifierType.SSN)

        assert result.valid is True
        assert result.metadata is not None

    @pytest.mark.parametrize(
        "tax_id",
        ["123-45-67890", "12345"],
        ids=["too_long", "too_short"],
    )
    def test_rejects_structurally_invalid_ssn(
        self,
        us_validator: TaxValidator,
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
        us_validator: TaxValidator,
        tax_id_factory: Callable[..., str],
        tax_id_type: TaxIdentifierType,
    ) -> None:
        """Test that a non-US identifier type is rejected."""

        with pytest.raises(UnsupportedTaxIdTypeError):
            us_validator.validate(tax_id_factory(TaxIdentifierType.SSN), tax_id_type)


class TestUsTaxRulesResolveMetadata:
    """Tests for resolving SSN metadata through US rules."""

    def test_resolves_known_ssn(self, allocated_ssn: AllocatedSsn) -> None:
        """Test that a known SSN resolves to issuing details."""

        metadata = UsTaxRules().resolve_metadata(allocated_ssn.tax_id, TaxIdentifierType.SSN)

        assert isinstance(metadata, SSNValidation)
        assert metadata.issued_state == allocated_ssn.issued_state

    def test_returns_none_for_invalid_ssn(self) -> None:
        """Test that an SSN without nine digits resolves to None."""

        assert UsTaxRules().resolve_metadata("12345", TaxIdentifierType.SSN) is None
