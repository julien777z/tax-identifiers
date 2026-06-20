import pytest

from tax_identifiers import (
    Country,
    GenericTaxRules,
    TaxIdentifierType,
    TaxValidator,
    UnsupportedTaxIdTypeError,
    get_country_rules,
)


class TestGenericTaxValidation:
    """Tests for tax identifiers of countries without dedicated rules."""

    def test_named_country_validation_is_not_implemented(self) -> None:
        """Test that validating a named country without dedicated rules raises NotImplementedError."""

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

    def test_unknown_country_uses_generic_rules(self) -> None:
        """Test that the UNKNOWN country dispatches to generic rules."""

        assert isinstance(get_country_rules(Country.UNKNOWN), GenericTaxRules)


class TestUnknownCountryValidation:
    """Tests for the country-agnostic UNKNOWN validation behavior."""

    def test_accepts_any_non_empty_identifier(self) -> None:
        """Test that the unknown country accepts any non-empty identifier as valid."""

        rules = GenericTaxRules(Country.UNKNOWN)

        assert rules.is_valid("FR1234567", TaxIdentifierType.FOREIGN_TIN) is True

    def test_rejects_empty_identifier(self) -> None:
        """Test that the unknown country treats an empty identifier as invalid."""

        rules = GenericTaxRules(Country.UNKNOWN)

        assert rules.is_valid("", TaxIdentifierType.FOREIGN_TIN) is False

    def test_validator_accepts_foreign_identifier_of_any_shape(self) -> None:
        """Test that the unknown-country validator accepts a foreign identifier of any shape."""

        validator = TaxValidator(Country.UNKNOWN)

        result = validator.validate("FR-12 34 AB", TaxIdentifierType.FOREIGN_TIN)

        assert result.country is Country.UNKNOWN
        assert result.valid is True
        assert result.metadata is None
