from collections.abc import Callable

import pytest

from tax_identifiers import TaxIdentifierType, match_us_tin


class TestMatchUsTin:
    """Tests for the US TIN match stub."""

    @pytest.mark.parametrize(
        "tax_id_type",
        [
            TaxIdentifierType.SSN,
            TaxIdentifierType.EIN,
            TaxIdentifierType.ITIN,
        ],
        ids=["ssn", "ein", "itin"],
    )
    async def test_raises_not_implemented(
        self,
        tax_id_type: TaxIdentifierType,
        tax_id_factory: Callable[..., str],
        full_name_factory: Callable[..., str],
    ) -> None:
        """Test that US TIN matching is not implemented yet and raises NotImplementedError."""

        with pytest.raises(NotImplementedError):
            await match_us_tin(
                full_name=full_name_factory(),
                tax_id=tax_id_factory(tax_id_type),
                tax_id_type=tax_id_type,
            )
