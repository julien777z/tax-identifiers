import pytest

from tax_identifiers import (
    Country,
    GenericTaxRules,
    InvalidTaxIdError,
    TaxIdentifierType,
    TaxValidator,
    UnsupportedTaxIdTypeError,
    get_country_rules,
)
from tests.factories import generate_tax_id


class TestGenericTaxValidation:
    """Test that countries without dedicated rules fall back to generic handling."""

    def test_named_country_reports_undecided_validity(self) -> None:
        """Test that a named country without dedicated rules reports validity as undecided."""

        validator = TaxValidator(Country.from_string("France"))

        result = validator.validate(
            generate_tax_id(TaxIdentifierType.FOREIGN_TIN), TaxIdentifierType.FOREIGN_TIN
        )

        assert result.valid is None

    def test_rejects_us_specific_type_for_generic_country(self) -> None:
        """Test that a US-specific identifier type is unsupported for a generic country."""

        validator = TaxValidator(Country.FR)

        with pytest.raises(UnsupportedTaxIdTypeError):
            validator.validate(generate_tax_id(TaxIdentifierType.SSN), TaxIdentifierType.SSN)


class TestGenericTaxRules:
    """Test that country-agnostic rules normalize and report validity."""

    def test_normalizes_to_uppercase(self) -> None:
        """Test that generic normalization collapses whitespace and uppercases."""

        rules = GenericTaxRules(Country.FR)

        assert rules.normalize("  fr-12 ab ", TaxIdentifierType.FOREIGN_TIN) == "FR-12 AB"

    def test_is_valid_is_undecided_for_a_named_country(self) -> None:
        """Test that validity is undecided without country-specific rules."""

        rules = GenericTaxRules(Country.FR)

        assert (
            rules.is_valid(
                generate_tax_id(TaxIdentifierType.FOREIGN_TIN), TaxIdentifierType.FOREIGN_TIN
            )
            is None
        )

    def test_resolves_no_metadata(self) -> None:
        """Test that generic rules resolve no country-specific metadata."""

        rules = GenericTaxRules(Country.FR)

        assert (
            rules.resolve_metadata(
                generate_tax_id(TaxIdentifierType.FOREIGN_TIN), TaxIdentifierType.FOREIGN_TIN
            )
            is None
        )

    def test_unknown_country_uses_generic_rules(self) -> None:
        """Test that the UNKNOWN country dispatches to generic rules."""

        assert isinstance(get_country_rules(Country.UNKNOWN), GenericTaxRules)


class TestUnknownCountryValidation:
    """Test that the UNKNOWN country accepts any non-empty identifier."""

    def test_accepts_any_non_empty_identifier(self) -> None:
        """Test that the unknown country accepts any non-empty identifier as valid."""

        rules = GenericTaxRules(Country.UNKNOWN)

        assert (
            rules.is_valid(
                generate_tax_id(TaxIdentifierType.FOREIGN_TIN), TaxIdentifierType.FOREIGN_TIN
            )
            is True
        )

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

    @pytest.mark.parametrize("tax_id", ["", "   "], ids=["empty", "whitespace"])
    def test_validator_rejects_empty_identifier(self, tax_id: str) -> None:
        """Test that the unknown-country validator rejects an empty identifier."""

        validator = TaxValidator(Country.UNKNOWN)

        with pytest.raises(InvalidTaxIdError):
            validator.validate(tax_id, TaxIdentifierType.FOREIGN_TIN)
