import pytest

from tax_identifiers import (
    ComparableUsTaxIdentifier,
    TaxIdentifierType,
    clean_us_tax_identifier,
    format_us_ein,
    format_us_ssn,
    is_us_tax_identifier_type,
    strict_format_us_ssn,
)
from tax_identifiers.normalization import strip_non_digits
from tests.factories import generate_tax_id


class TestStripNonDigits:
    """Test that non-digit characters are stripped."""

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
    """Test that a US tax identifier normalizes to nine digits."""

    def test_normalizes_formatted_identifier_to_digits(
        self,
    ) -> None:
        """Test that a formatted identifier is normalized to bare digits."""

        raw_tax_id = generate_tax_id(TaxIdentifierType.SSN)

        assert clean_us_tax_identifier(format_us_ssn(raw_tax_id)) == raw_tax_id

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
    """Test that SSNs are formatted progressively as digits are entered."""

    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            ("123", "123"),
            ("12345", "123-45"),
        ],
        ids=["area", "area_group"],
    )
    def test_inserts_dashes_as_digits_are_entered(self, value: str, expected: str) -> None:
        """Test that dashes are inserted progressively as digits are provided."""

        assert format_us_ssn(value) == expected

    def test_formats_full_identifier(self) -> None:
        """Test that a nine-digit identifier is formatted as XXX-XX-XXXX."""

        raw_tax_id = generate_tax_id(TaxIdentifierType.SSN)

        assert format_us_ssn(raw_tax_id) == f"{raw_tax_id[:3]}-{raw_tax_id[3:5]}-{raw_tax_id[5:]}"

    def test_returns_none_for_empty_input(self) -> None:
        """Test that empty input resolves to None."""

        assert format_us_ssn("") is None


class TestStrictFormatUsSsn:
    """Test that strict SSN formatting requires nine digits."""

    def test_formats_nine_digit_ssn(self) -> None:
        """Test that a nine-digit SSN is formatted with dashes."""

        raw_tax_id = generate_tax_id(TaxIdentifierType.SSN)

        assert strict_format_us_ssn(raw_tax_id) == f"{raw_tax_id[:3]}-{raw_tax_id[3:5]}-{raw_tax_id[5:]}"

    def test_rejects_partial_ssn(self) -> None:
        """Test that an SSN without nine digits raises an error."""

        with pytest.raises(ValueError):
            strict_format_us_ssn("12345")


class TestFormatUsEin:
    """Test that EINs are formatted correctly."""

    def test_formats_nine_digit_ein(self) -> None:
        """Test that a nine-digit EIN is formatted as XX-XXXXXXX."""

        raw_tax_id = generate_tax_id(TaxIdentifierType.EIN)

        assert format_us_ein(raw_tax_id) == f"{raw_tax_id[:2]}-{raw_tax_id[2:]}"


class TestComparableUsTaxIdentifier:
    """Test that tax identifier comparison ignores formatting."""

    def test_equals_across_formatting(self) -> None:
        """Test that dashed and bare forms compare equal."""

        raw_tax_id = generate_tax_id(TaxIdentifierType.SSN)

        assert ComparableUsTaxIdentifier(format_us_ssn(raw_tax_id)) == raw_tax_id

    def test_hashes_equal_across_formatting(self) -> None:
        """Test that dashed and bare forms hash to the same value."""

        raw_tax_id = generate_tax_id(TaxIdentifierType.SSN)

        assert hash(ComparableUsTaxIdentifier(format_us_ssn(raw_tax_id))) == hash(
            ComparableUsTaxIdentifier(raw_tax_id)
        )

    def test_not_equal_to_invalid_string(self) -> None:
        """Test that a malformed comparison value is never equal."""

        raw_tax_id = generate_tax_id(TaxIdentifierType.SSN)

        assert ComparableUsTaxIdentifier(raw_tax_id) != "not-a-tax-id"


class TestIsUsTaxIdentifierType:
    """Test that US tax identifier types are classified correctly."""

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
