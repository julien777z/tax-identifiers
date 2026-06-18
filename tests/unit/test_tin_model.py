import pytest

from tax_validation import (
    ComparableUsTaxIdentifier,
    TaxIdentifierModel,
    TaxIdentifierType,
)


class TestTaxIdentifierModelValid:
    """Tests for the reserved-range validity check."""

    @pytest.mark.parametrize(
        ("tax_id", "expected"),
        [
            ("123-45-6789", True),
            ("000-12-3456", False),
            ("666-12-3456", False),
            ("900-12-3456", False),
            ("123-00-6789", False),
            ("123-45-0000", False),
        ],
        ids=["valid", "area_000", "area_666", "area_900", "group_00", "serial_0000"],
    )
    def test_flags_reserved_ssn_ranges(self, tax_id: str, expected: bool) -> None:
        """Test that reserved SSN area, group, and serial values are flagged invalid."""

        model = TaxIdentifierModel(tax_id=tax_id, tax_id_type=TaxIdentifierType.SSN)

        assert model.valid is expected

    @pytest.mark.parametrize(
        "tax_id_type",
        [TaxIdentifierType.EIN, TaxIdentifierType.ITIN, TaxIdentifierType.US_UNSPECIFIED],
        ids=["ein", "itin", "us_unspecified"],
    )
    def test_non_ssn_us_types_are_valid(self, tax_id_type: TaxIdentifierType) -> None:
        """Test that non-SSN US identifier types skip reserved-range checks."""

        model = TaxIdentifierModel(tax_id="123456789", tax_id_type=tax_id_type)

        assert model.valid is True


class TestTaxIdentifierModelSsnValidation:
    """Tests for derived SSN validation details."""

    def test_resolves_issuing_details_for_ssn(self) -> None:
        """Test that an SSN exposes resolved allocation details."""

        model = TaxIdentifierModel(tax_id="001-01-0001", tax_id_type=TaxIdentifierType.SSN)

        assert model.ssn_validation is not None
        assert model.ssn_validation.issued_state is not None

    def test_returns_none_for_non_ssn(self) -> None:
        """Test that non-SSN identifiers expose no SSN validation."""

        model = TaxIdentifierModel(tax_id="123456789", tax_id_type=TaxIdentifierType.EIN)

        assert model.ssn_validation is None


class TestTaxIdentifierModelNormalization:
    """Tests for tax identifier normalization on construction."""

    def test_us_identifier_is_comparable(self) -> None:
        """Test that a US identifier is stored as a formatting-insensitive value."""

        model = TaxIdentifierModel(tax_id="123-45-6789", tax_id_type=TaxIdentifierType.SSN)

        assert isinstance(model.tax_id, ComparableUsTaxIdentifier)
        assert model.tax_id == "123456789"

    def test_foreign_identifier_is_uppercased(self) -> None:
        """Test that a foreign identifier is normalized to uppercase."""

        model = TaxIdentifierModel(tax_id=" gb-12 ", tax_id_type=TaxIdentifierType.FOREIGN_TIN)

        assert model.tax_id == "GB-12"


class TestTaxIdentifierModelEquality:
    """Tests for equality and hashing semantics."""

    def test_equals_matching_model(self) -> None:
        """Test that models with the same type and identifier compare equal."""

        left = TaxIdentifierModel(tax_id="123-45-6789", tax_id_type=TaxIdentifierType.SSN)
        right = TaxIdentifierModel(tax_id="123456789", tax_id_type=TaxIdentifierType.SSN)

        assert left == right

    def test_equals_normalized_string(self) -> None:
        """Test that a model compares equal to its normalized string form."""

        model = TaxIdentifierModel(tax_id="123-45-6789", tax_id_type=TaxIdentifierType.SSN)

        assert model == "123456789"
