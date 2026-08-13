import pytest

from tax_identifiers import (
    TaxIdentifierOrigin,
    TaxIdentifierType,
    TinType,
    format_us_ssn,
)
from tax_identifiers.normalization import (
    collapse_whitespace,
    empty_str_to_none,
    transform_required_string,
)
from tax_identifiers.us.transformers import transform_tax_identifier
from tests.factories import generate_tax_id


class TestCollapseWhitespace:
    """Test that whitespace is collapsed."""

    def test_collapses_internal_and_edge_whitespace(self) -> None:
        """Test that runs of whitespace collapse to single spaces and trim."""

        assert collapse_whitespace("  a   b  ") == "a b"


class TestTransformRequiredString:
    """Test that required strings are normalized and empties rejected."""

    @pytest.mark.parametrize("value", [None, "", "   "], ids=["none", "empty", "whitespace"])
    def test_rejects_empty_values(self, value: str | None) -> None:
        """Test that empty or whitespace-only values are rejected."""

        with pytest.raises(ValueError):
            transform_required_string(value)


class TestEmptyStrToNone:
    """Test that empty strings convert to None."""

    def test_converts_blank_strings(self) -> None:
        """Test that blank string values become None while others are preserved."""

        result = empty_str_to_none({"a": "  ", "b": "x", "c": 1})

        assert result == {"a": None, "b": "x", "c": 1}

    def test_does_not_mutate_input(self) -> None:
        """Test that the input mapping is left unchanged."""

        original = {"a": "  ", "b": "x"}
        empty_str_to_none(original)

        assert original == {"a": "  ", "b": "x"}


class TestTransformTaxIdentifier:
    """Test that tax identifier normalization respects the origin."""

    def test_cleans_us_identifier_to_digits(self) -> None:
        """Test that a US identifier normalizes to nine bare digits."""

        raw_tax_id = generate_tax_id(TaxIdentifierType.SSN)

        result = transform_tax_identifier(format_us_ssn(raw_tax_id), origin=TaxIdentifierOrigin.US_TIN)

        assert result == raw_tax_id

    def test_uppercases_foreign_identifier(self) -> None:
        """Test that a foreign identifier is normalized to uppercase."""

        result = transform_tax_identifier(" gb12 ", origin=TaxIdentifierOrigin.FOREIGN_TIN)

        assert result == "GB12"

    def test_rejects_mask_characters(self) -> None:
        """Test that mask characters are rejected."""

        with pytest.raises(ValueError):
            transform_tax_identifier("***45678", origin=TaxIdentifierOrigin.US_TIN)

    def test_returns_none_for_missing_value(self) -> None:
        """Test that a missing value resolves to None."""

        assert transform_tax_identifier(None, origin=TaxIdentifierOrigin.FOREIGN_TIN) is None

    def test_foreign_origin_with_ssn_subtype_is_cleaned(
        self,
    ) -> None:
        """Test that an SSN subtype forces US cleaning even for foreign origin."""

        raw_tax_id = generate_tax_id(TaxIdentifierType.SSN)

        result = transform_tax_identifier(
            format_us_ssn(raw_tax_id),
            origin=TaxIdentifierOrigin.FOREIGN_TIN,
            tin_type=TinType.SSN,
        )

        assert result == raw_tax_id
