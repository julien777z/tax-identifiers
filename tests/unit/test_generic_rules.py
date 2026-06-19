import pytest

from tax_validation import (
    Country,
    GenericTaxRules,
    TaxIdentifierType,
    TaxValidator,
    UnsupportedTaxIdTypeError,
)


class TestGenericTaxValidation:
    """Tests for validating tax identifiers of countries without dedicated rules."""

    def test_validates_foreign_tin_generically(self) -> None:
        """Test that a foreign TIN for a generic country validates and reports the country."""

        validator = TaxValidator(Country.from_string("France"))

        result = validator.validate("fr1234567", TaxIdentifierType.FOREIGN_TIN)

        assert result.country == Country.FR
        assert result.valid is True
        assert result.metadata is None

    def test_rejects_us_specific_type_for_generic_country(self) -> None:
        """Test that a US-specific identifier type is unsupported for a generic country."""

        validator = TaxValidator(Country.FR)

        with pytest.raises(UnsupportedTaxIdTypeError):
            validator.validate("123-45-6789", TaxIdentifierType.SSN)


class TestGenericTaxRules:
    """Tests for the country-agnostic normalization and validity checks."""

    def test_normalizes_to_uppercase(self) -> None:
        """Test that generic normalization collapses whitespace and uppercases."""

        rules = GenericTaxRules(Country.FR)

        assert rules.normalize("  fr-12 ab ", TaxIdentifierType.FOREIGN_TIN) == "FR-12 AB"

    @pytest.mark.parametrize(
        "tax_id",
        ["", "   ", "*"],
        ids=["empty", "whitespace", "non_alphanumeric"],
    )
    def test_rejects_implausible_identifier(self, tax_id: str) -> None:
        """Test that empty or non-alphanumeric identifiers are not valid."""

        rules = GenericTaxRules(Country.FR)

        assert rules.is_valid(tax_id, TaxIdentifierType.FOREIGN_TIN) is False

    def test_resolves_no_metadata(self) -> None:
        """Test that generic rules resolve no country-specific metadata."""

        rules = GenericTaxRules(Country.FR)

        assert rules.resolve_metadata("fr1234567", TaxIdentifierType.FOREIGN_TIN) is None
