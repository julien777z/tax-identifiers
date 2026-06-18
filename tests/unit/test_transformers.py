from collections.abc import Callable

import pytest

from tax_validation import (
    TaxIdentifierOrigin,
    TaxIdentifierType,
    TinType,
    build_string_normalizer,
    collapse_whitespace,
    empty_str_to_none,
    format_us_ssn,
    transform_required_string,
    transform_tax_identifier,
)


class TestCollapseWhitespace:
    """Tests for whitespace collapsing."""

    def test_collapses_internal_and_edge_whitespace(self) -> None:
        """Test that runs of whitespace collapse to single spaces and trim."""

        assert collapse_whitespace("  a   b  ") == "a b"

    def test_rejects_non_string(self) -> None:
        """Test that a non-string value raises an error."""

        with pytest.raises(ValueError):
            collapse_whitespace(123)


class TestTransformRequiredString:
    """Tests for required-string normalization."""

    @pytest.mark.parametrize("value", [None, "", "   "], ids=["none", "empty", "whitespace"])
    def test_rejects_empty_values(self, value: str | None) -> None:
        """Test that empty or whitespace-only values are rejected."""

        with pytest.raises(ValueError):
            transform_required_string(value)


class TestBuildStringNormalizer:
    """Tests for the composable string normalizer."""

    @pytest.mark.parametrize(
        ("options", "value", "expected"),
        [
            ({"normalize_to_lowercase": True}, "ABC", "abc"),
            ({"normalize_to_titlecase": True}, "john doe", "John Doe"),
            ({"strip_non_digits": True}, "a1b2", "12"),
            ({"strip_trailing_punctuation": True}, "ave. st,", "ave st"),
        ],
        ids=["lowercase", "titlecase", "strip_non_digits", "strip_trailing_punctuation"],
    )
    def test_applies_selected_options(
        self,
        options: dict[str, bool],
        value: str,
        expected: str,
    ) -> None:
        """Test that the normalizer applies the configured transformations."""

        normalizer = build_string_normalizer(**options)

        assert normalizer(value) == expected


class TestEmptyStrToNone:
    """Tests for empty-string to None conversion."""

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
    """Tests for origin-aware tax identifier normalization."""

    def test_cleans_us_identifier_to_digits(self, tax_id_factory: Callable[..., str]) -> None:
        """Test that a US identifier normalizes to nine bare digits."""

        raw_tax_id = tax_id_factory(TaxIdentifierType.SSN)

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
        tax_id_factory: Callable[..., str],
    ) -> None:
        """Test that an SSN subtype forces US cleaning even for foreign origin."""

        raw_tax_id = tax_id_factory(TaxIdentifierType.SSN)

        result = transform_tax_identifier(
            format_us_ssn(raw_tax_id),
            origin=TaxIdentifierOrigin.FOREIGN_TIN,
            tin_type=TinType.SSN,
        )

        assert result == raw_tax_id
