import pytest

from tax_validation import (
    ComparableUsTaxIdentifier,
    TaxIdentifierType,
    clean_us_tax_identifier,
    format_us_ein,
    format_us_ssn,
    is_us_tax_identifier_type,
    strict_format_us_ssn,
    strip_non_digits,
)


class TestStripNonDigits:
    """Tests for stripping non-digit characters."""

    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            ("123-45-6789", "123456789"),
            (" 12 34 ", "1234"),
            ("abc", ""),
        ],
        ids=["dashes", "spaces", "letters"],
    )
    def test_removes_non_digit_characters(self, value: str, expected: str) -> None:
        """Test that non-digit characters are removed from the input."""

        assert strip_non_digits(value) == expected


class TestCleanUsTaxIdentifier:
    """Tests for normalizing a US tax identifier to nine digits."""

    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            ("123-45-6789", "123456789"),
            (" 123456789 ", "123456789"),
            (123456789, "123456789"),
        ],
        ids=["dashed", "padded", "int"],
    )
    def test_normalizes_nine_digit_values(self, value: str | int, expected: str) -> None:
        """Test that a nine-digit identifier is normalized to bare digits."""

        assert clean_us_tax_identifier(value) == expected

    @pytest.mark.parametrize("value", [None, "", 0], ids=["none", "empty", "zero"])
    def test_returns_none_for_empty_values(self, value: str | int | None) -> None:
        """Test that empty inputs resolve to None."""

        assert clean_us_tax_identifier(value) is None

    @pytest.mark.parametrize("value", ["12345", "1234567890"], ids=["too_short", "too_long"])
    def test_rejects_values_that_are_not_nine_digits(self, value: str) -> None:
        """Test that an identifier without exactly nine digits raises an error."""

        with pytest.raises(ValueError):
            clean_us_tax_identifier(value)


class TestFormatUsSsn:
    """Tests for progressive SSN formatting."""

    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            ("123", "123"),
            ("12345", "123-45"),
            ("123456789", "123-45-6789"),
            ("123-45-6789", "123-45-6789"),
        ],
        ids=["area", "area_group", "full", "already_dashed"],
    )
    def test_inserts_dashes_as_digits_are_entered(self, value: str, expected: str) -> None:
        """Test that dashes are inserted progressively as digits are provided."""

        assert format_us_ssn(value) == expected

    def test_returns_none_for_empty_input(self) -> None:
        """Test that empty input resolves to None."""

        assert format_us_ssn("") is None


class TestStrictFormatUsSsn:
    """Tests for strict nine-digit SSN formatting."""

    def test_formats_nine_digit_ssn(self) -> None:
        """Test that a nine-digit SSN is formatted with dashes."""

        assert strict_format_us_ssn("123456789") == "123-45-6789"

    def test_rejects_partial_ssn(self) -> None:
        """Test that an SSN without nine digits raises an error."""

        with pytest.raises(ValueError):
            strict_format_us_ssn("12345")


class TestFormatUsEin:
    """Tests for EIN formatting."""

    def test_formats_nine_digit_ein(self) -> None:
        """Test that a nine-digit EIN is formatted as XX-XXXXXXX."""

        assert format_us_ein("123456789") == "12-3456789"


class TestComparableUsTaxIdentifier:
    """Tests for formatting-insensitive tax identifier comparison."""

    def test_equals_across_formatting(self) -> None:
        """Test that dashed and bare forms compare equal."""

        assert ComparableUsTaxIdentifier("123-45-6789") == "123456789"

    def test_hashes_equal_across_formatting(self) -> None:
        """Test that dashed and bare forms hash to the same value."""

        assert hash(ComparableUsTaxIdentifier("123-45-6789")) == hash(
            ComparableUsTaxIdentifier("123456789")
        )

    def test_not_equal_to_different_identifier(self) -> None:
        """Test that distinct identifiers do not compare equal."""

        assert ComparableUsTaxIdentifier("123-45-6789") != "987654321"


class TestIsUsTaxIdentifierType:
    """Tests for classifying US tax identifier types."""

    @pytest.mark.parametrize(
        ("tax_id_type", "expected"),
        [
            (TaxIdentifierType.SSN, True),
            (TaxIdentifierType.EIN, True),
            (TaxIdentifierType.ITIN, True),
            (TaxIdentifierType.US_UNSPECIFIED, True),
            (TaxIdentifierType.FOREIGN_TIN, False),
            (TaxIdentifierType.NONE, False),
        ],
        ids=["ssn", "ein", "itin", "us_unspecified", "foreign", "none"],
    )
    def test_classifies_us_types(self, tax_id_type: TaxIdentifierType, expected: bool) -> None:
        """Test that US identifier types are distinguished from foreign and none."""

        assert is_us_tax_identifier_type(tax_id_type) is expected
