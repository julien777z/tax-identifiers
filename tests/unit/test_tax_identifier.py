import pytest

from tax_identifiers import (
    ComparableUsTaxIdentifier,
    Country,
    TaxIdentifier,
    TaxIdentifierType,
    format_us_ssn,
)
from tests.factories import (
    TaxIdentifierFactory,
    generate_tax_id,
)


class TestTaxIdentifierValid:
    """Test that reserved SSN ranges are reported invalid."""

    @pytest.mark.parametrize(
        "tax_id",
        ["000-12-3456", "666-12-3456", "900-12-3456", "123-00-6789", "123-45-0000"],
        ids=["area_000", "area_666", "area_900", "group_00", "serial_0000"],
    )
    def test_flags_reserved_ssn_ranges(self, tax_id: str) -> None:
        """Test that reserved SSN area, group, and serial values are flagged invalid."""

        identifier = TaxIdentifier(
            country=Country.US,
            tax_id=tax_id,
            tax_id_type=TaxIdentifierType.SSN,
        )

        assert identifier.valid is False

    def test_generated_ssn_is_valid(
        self,
    ) -> None:
        """Test that a structurally sound SSN passes the validity check."""

        identifier = TaxIdentifierFactory.build(tax_id_type=TaxIdentifierType.SSN)

        assert identifier.valid is True

    @pytest.mark.parametrize(
        "tax_id_type",
        [TaxIdentifierType.EIN, TaxIdentifierType.ITIN, TaxIdentifierType.US_UNSPECIFIED],
        ids=["ein", "itin", "us_unspecified"],
    )
    def test_non_ssn_us_types_are_valid(
        self,
        tax_id_type: TaxIdentifierType,
    ) -> None:
        """Test that non-SSN US identifier types skip reserved-range checks."""

        identifier = TaxIdentifierFactory.build(tax_id_type=tax_id_type)

        assert identifier.valid is True


class TestTaxIdentifierMetadata:
    """Test that SSN metadata is derived from an identifier."""

    def test_exposes_metadata_for_ssn(
        self,
    ) -> None:
        """Test that an SSN exposes a resolved metadata object."""

        identifier = TaxIdentifierFactory.build(tax_id_type=TaxIdentifierType.SSN)

        assert identifier.metadata is not None

    def test_returns_none_for_non_ssn(
        self,
    ) -> None:
        """Test that non-SSN identifiers expose no metadata."""

        identifier = TaxIdentifierFactory.build(tax_id_type=TaxIdentifierType.EIN)

        assert identifier.metadata is None


class TestTaxIdentifierNormalization:
    """Test that a tax identifier is normalized on construction."""

    def test_us_identifier_is_comparable(
        self,
    ) -> None:
        """Test that a US identifier is stored as a formatting-insensitive value."""

        raw_tax_id = generate_tax_id(TaxIdentifierType.SSN)
        identifier = TaxIdentifier(
            country=Country.US,
            tax_id=format_us_ssn(raw_tax_id),
            tax_id_type=TaxIdentifierType.SSN,
        )

        assert isinstance(identifier.tax_id, ComparableUsTaxIdentifier)
        assert identifier.tax_id == raw_tax_id

    def test_foreign_identifier_is_uppercased(self) -> None:
        """Test that a foreign-typed identifier is normalized to uppercase."""

        identifier = TaxIdentifier(
            country=Country.US,
            tax_id=" gb-12 ",
            tax_id_type=TaxIdentifierType.FOREIGN_TIN,
        )

        assert identifier.tax_id == "GB-12"


class TestTaxIdentifierEquality:
    """Test that equality and hashing compare on the normalized identifier."""

    def test_equals_matching_model_across_formatting(
        self,
    ) -> None:
        """Test that dashed and bare forms of the same SSN compare equal."""

        raw_tax_id = generate_tax_id(TaxIdentifierType.SSN)
        left = TaxIdentifier(
            country=Country.US,
            tax_id=format_us_ssn(raw_tax_id),
            tax_id_type=TaxIdentifierType.SSN,
        )
        right = TaxIdentifier(
            country=Country.US,
            tax_id=raw_tax_id,
            tax_id_type=TaxIdentifierType.SSN,
        )

        assert left == right

    def test_equals_normalized_string(
        self,
    ) -> None:
        """Test that a model compares equal to its normalized string form."""

        raw_tax_id = generate_tax_id(TaxIdentifierType.SSN)
        identifier = TaxIdentifier(
            country=Country.US,
            tax_id=format_us_ssn(raw_tax_id),
            tax_id_type=TaxIdentifierType.SSN,
        )

        assert identifier == raw_tax_id

    def test_differs_by_tax_id_type(
        self,
    ) -> None:
        """Test that the same digits under different types are not equal."""

        raw_tax_id = generate_tax_id(TaxIdentifierType.SSN)
        ssn = TaxIdentifier(
            country=Country.US, tax_id=raw_tax_id, tax_id_type=TaxIdentifierType.SSN
        )
        ein = TaxIdentifier(
            country=Country.US, tax_id=raw_tax_id, tax_id_type=TaxIdentifierType.EIN
        )

        assert ssn != ein

    def test_is_hashable_consistently_with_string(
        self,
    ) -> None:
        """Test that a model hashes consistently with its normalized identifier."""

        raw_tax_id = generate_tax_id(TaxIdentifierType.SSN)
        identifier = TaxIdentifier(
            country=Country.US,
            tax_id=raw_tax_id,
            tax_id_type=TaxIdentifierType.SSN,
        )

        assert hash(identifier) == hash(raw_tax_id)
        assert identifier in {identifier}
