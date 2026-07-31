import pytest

from tax_identifiers import TaxIdentifierType, match_us_tin
from tests.factories import (
    generate_full_name,
    generate_tax_id,
)


class TestMatchUsTin:
    """Test that US TIN matching reports it is not implemented."""

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
    ) -> None:
        """Test that US TIN matching is not implemented yet and raises NotImplementedError."""

        with pytest.raises(NotImplementedError):
            await match_us_tin(
                full_name=generate_full_name(),
                tax_id=generate_tax_id(tax_id_type),
                tax_id_type=tax_id_type,
            )
