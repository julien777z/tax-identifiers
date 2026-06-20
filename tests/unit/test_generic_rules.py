import pytest

from tax_identifiers import (
    Country,
    GenericTaxRules,
    TaxIdentifierType,
    TaxValidator,
    UnsupportedTaxIdTypeError,
)


class TestGenericTaxValidation:
    """Tests for tax identifiers of countries without dedicated rules."""

    def test_validation_is_not_implemented(self) -> None:
        """Test that validating a country without dedicated rules raises NotImplementedError."""

        validator = TaxValidator(Country.from_string("France"))

        with pytest.raises(NotImplementedError):
            validator.validate("FR1234567", TaxIdentifierType.FOREIGN_TIN)

    def test_rejects_us_specific_type_for_generic_country(self) -> None:
        """Test that a US-specific identifier type is unsupported for a generic country."""

        validator = TaxValidator(Country.FR)

        with pytest.raises(UnsupportedTaxIdTypeError):
            validator.validate("123-45-6789", TaxIdentifierType.SSN)


class TestGenericTaxRules:
    """Tests for the country-agnostic normalization and validity behavior."""

    def test_normalizes_to_uppercase(self) -> None:
        """Test that generic normalization collapses whitespace and uppercases."""

        rules = GenericTaxRules(Country.FR)

        assert rules.normalize("  fr-12 ab ", TaxIdentifierType.FOREIGN_TIN) == "FR-12 AB"

    def test_is_valid_is_not_implemented(self) -> None:
        """Test that validity cannot be determined without country-specific rules."""

        rules = GenericTaxRules(Country.FR)

        with pytest.raises(NotImplementedError):
            rules.is_valid("FR1234567", TaxIdentifierType.FOREIGN_TIN)

    def test_resolves_no_metadata(self) -> None:
        """Test that generic rules resolve no country-specific metadata."""

        rules = GenericTaxRules(Country.FR)

        assert rules.resolve_metadata("fr1234567", TaxIdentifierType.FOREIGN_TIN) is None
