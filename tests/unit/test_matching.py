import asyncio
from collections.abc import Callable

import pytest

from tax_identifiers import (
    InvalidTaxIdError,
    TaxIdentifierType,
    UnsupportedTaxIdTypeError,
    match_us_tin,
)

FULL_NAME = "Jane Q Contractor"


class TestMatchUsTin:
    """Tests for the placeholder US TIN match."""

    @pytest.mark.parametrize(
        "tax_id_type",
        [
            TaxIdentifierType.SSN,
            TaxIdentifierType.EIN,
            TaxIdentifierType.ITIN,
        ],
        ids=["ssn", "ein", "itin"],
    )
    def test_returns_true_for_matching_us_tin(
        self,
        tax_id_type: TaxIdentifierType,
        tax_id_factory: Callable[..., str],
    ) -> None:
        """Test that a US name and TIN pair matches when the TIN is not the failure sentinel."""

        result = asyncio.run(
            match_us_tin(full_name=FULL_NAME, tax_id="123-45-6789", tax_id_type=tax_id_type)
        )

        assert result is True

    def test_returns_false_for_failure_sentinel(self) -> None:
        """Test that a TIN ending in the failure sentinel does not match."""

        result = asyncio.run(
            match_us_tin(full_name=FULL_NAME, tax_id="123-45-0000", tax_id_type=TaxIdentifierType.SSN)
        )

        assert result is False

    def test_rejects_non_us_tax_identifier_type(self) -> None:
        """Test that a non-US tax identifier type raises an unsupported type error."""

        with pytest.raises(UnsupportedTaxIdTypeError):
            asyncio.run(
                match_us_tin(
                    full_name=FULL_NAME,
                    tax_id="123456789",
                    tax_id_type=TaxIdentifierType.FOREIGN_TIN,
                )
            )

    @pytest.mark.parametrize(
        "tax_id",
        ["12345", "123-45-67890"],
        ids=["too_short", "too_long"],
    )
    def test_rejects_structurally_invalid_tin(self, tax_id: str) -> None:
        """Test that a TIN without nine digits raises an invalid tax id error."""

        with pytest.raises(InvalidTaxIdError):
            asyncio.run(
                match_us_tin(full_name=FULL_NAME, tax_id=tax_id, tax_id_type=TaxIdentifierType.SSN)
            )

    def test_rejects_missing_full_name(self) -> None:
        """Test that a blank full name raises an invalid tax id error."""

        with pytest.raises(InvalidTaxIdError):
            asyncio.run(
                match_us_tin(full_name="   ", tax_id="123-45-6789", tax_id_type=TaxIdentifierType.SSN)
            )
