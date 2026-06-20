from collections.abc import Callable

import pytest

from tax_identifiers import (
    ComparableUsTaxIdentifier,
    Country,
    TaxIdentifier,
    TaxIdentifierType,
    format_us_ssn,
)


class TestTaxIdentifierValid:
    """Tests for the reserved-range validity check."""

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
        tax_identifier_factory: Callable[..., TaxIdentifier],
    ) -> None:
        """Test that a structurally sound SSN passes the validity check."""

        identifier = tax_identifier_factory(TaxIdentifierType.SSN)

        assert identifier.valid is True

    @pytest.mark.parametrize(
        "tax_id_type",
        [TaxIdentifierType.EIN, TaxIdentifierType.ITIN, TaxIdentifierType.US_UNSPECIFIED],
        ids=["ein", "itin", "us_unspecified"],
    )
    def test_non_ssn_us_types_are_valid(
        self,
        tax_identifier_factory: Callable[..., TaxIdentifier],
        tax_id_type: TaxIdentifierType,
    ) -> None:
        """Test that non-SSN US identifier types skip reserved-range checks."""

        identifier = tax_identifier_factory(tax_id_type)

        assert identifier.valid is True


class TestTaxIdentifierMetadata:
    """Tests for derived SSN metadata."""

    def test_exposes_metadata_for_ssn(
        self,
        tax_identifier_factory: Callable[..., TaxIdentifier],
    ) -> None:
        """Test that an SSN exposes a resolved metadata object."""

        identifier = tax_identifier_factory(TaxIdentifierType.SSN)

        assert identifier.metadata is not None

    def test_returns_none_for_non_ssn(
        self,
        tax_identifier_factory: Callable[..., TaxIdentifier],
    ) -> None:
        """Test that non-SSN identifiers expose no metadata."""

        identifier = tax_identifier_factory(TaxIdentifierType.EIN)

        assert identifier.metadata is None


class TestTaxIdentifierNormalization:
    """Tests for tax identifier normalization on construction."""

    def test_us_identifier_is_comparable(
        self,
        tax_id_factory: Callable[..., str],
    ) -> None:
        """Test that a US identifier is stored as a formatting-insensitive value."""

        raw_tax_id = tax_id_factory(TaxIdentifierType.SSN)
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
    """Tests for equality and hashing semantics."""

    def test_equals_matching_model_across_formatting(
        self,
        tax_id_factory: Callable[..., str],
    ) -> None:
        """Test that dashed and bare forms of the same SSN compare equal."""

        raw_tax_id = tax_id_factory(TaxIdentifierType.SSN)
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
        tax_id_factory: Callable[..., str],
    ) -> None:
        """Test that a model compares equal to its normalized string form."""

        raw_tax_id = tax_id_factory(TaxIdentifierType.SSN)
        identifier = TaxIdentifier(
            country=Country.US,
            tax_id=format_us_ssn(raw_tax_id),
            tax_id_type=TaxIdentifierType.SSN,
        )

        assert identifier == raw_tax_id

    def test_differs_by_tax_id_type(
        self,
        tax_id_factory: Callable[..., str],
    ) -> None:
        """Test that the same digits under different types are not equal."""

        raw_tax_id = tax_id_factory(TaxIdentifierType.SSN)
        ssn = TaxIdentifier(country=Country.US, tax_id=raw_tax_id, tax_id_type=TaxIdentifierType.SSN)
        ein = TaxIdentifier(country=Country.US, tax_id=raw_tax_id, tax_id_type=TaxIdentifierType.EIN)

        assert ssn != ein

    def test_is_hashable_consistently_with_string(
        self,
        tax_id_factory: Callable[..., str],
    ) -> None:
        """Test that a model hashes consistently with its normalized identifier."""

        raw_tax_id = tax_id_factory(TaxIdentifierType.SSN)
        identifier = TaxIdentifier(
            country=Country.US,
            tax_id=raw_tax_id,
            tax_id_type=TaxIdentifierType.SSN,
        )

        assert hash(identifier) == hash(raw_tax_id)
        assert identifier in {identifier}
