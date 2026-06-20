from collections.abc import Callable

import pytest

from tax_identifiers import Country, TaxIdentifierType, TaxValidationResult


class TestTaxValidationResultFromTaxIdentifier:
    """Tests for building a validation summary from a raw identifier."""

    def test_summarizes_valid_ssn(self, tax_id_factory: Callable[..., str]) -> None:
        """Test that a valid SSN produces a summary with resolved details."""

        summary = TaxValidationResult.from_tax_identifier(
            country=Country.US,
            tax_id=tax_id_factory(TaxIdentifierType.SSN),
            tax_id_type=TaxIdentifierType.SSN,
        )

        assert summary is not None
        assert summary.country == Country.US
        assert summary.tax_id_type == TaxIdentifierType.SSN
        assert summary.valid is True
        assert summary.metadata is not None

    def test_summarizes_reserved_ssn_as_invalid(self) -> None:
        """Test that a structurally reserved SSN is summarized as invalid."""

        summary = TaxValidationResult.from_tax_identifier(
            country=Country.US,
            tax_id="666-12-3456",
            tax_id_type=TaxIdentifierType.SSN,
        )

        assert summary is not None
        assert summary.valid is False

    def test_returns_none_for_malformed_identifier(self) -> None:
        """Test that an identifier without nine digits resolves to None."""

        summary = TaxValidationResult.from_tax_identifier(
            country=Country.US,
            tax_id="123",
            tax_id_type=TaxIdentifierType.SSN,
        )

        assert summary is None

    @pytest.mark.parametrize(
        ("provide_id", "provide_type"),
        [(False, True), (True, False)],
        ids=["missing_id", "missing_type"],
    )
    def test_returns_none_when_inputs_absent(
        self,
        tax_id_factory: Callable[..., str],
        provide_id: bool,
        provide_type: bool,
    ) -> None:
        """Test that a missing identifier or type resolves to None."""

        summary = TaxValidationResult.from_tax_identifier(
            country=Country.US,
            tax_id=tax_id_factory(TaxIdentifierType.SSN) if provide_id else None,
            tax_id_type=TaxIdentifierType.SSN if provide_type else None,
        )

        assert summary is None

    @pytest.mark.parametrize(
        "country",
        [Country.UNKNOWN, Country.FR],
        ids=["unknown", "named_without_rules"],
    )
    @pytest.mark.parametrize("tax_id", ["", "   "], ids=["empty", "whitespace"])
    def test_returns_none_for_empty_identifier(self, country: Country, tax_id: str) -> None:
        """Test that an empty or whitespace identifier resolves to None for any country."""

        summary = TaxValidationResult.from_tax_identifier(
            country=country,
            tax_id=tax_id,
            tax_id_type=TaxIdentifierType.FOREIGN_TIN,
        )

        assert summary is None

    def test_excludes_raw_tax_id_from_summary(self, tax_id_factory: Callable[..., str]) -> None:
        """Test that the serialized summary does not expose the raw tax identifier."""

        summary = TaxValidationResult.from_tax_identifier(
            country=Country.US,
            tax_id=tax_id_factory(TaxIdentifierType.SSN),
            tax_id_type=TaxIdentifierType.SSN,
        )

        assert summary is not None
        assert "tax_id" not in summary.model_dump()

    def test_raises_for_country_without_rules(self) -> None:
        """Test that summarizing a country without dedicated rules raises NotImplementedError."""

        with pytest.raises(NotImplementedError):
            TaxValidationResult.from_tax_identifier(
                country=Country.FR,
                tax_id="FR1234567",
                tax_id_type=TaxIdentifierType.FOREIGN_TIN,
            )
