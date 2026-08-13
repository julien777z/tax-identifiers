from collections.abc import Callable
from tax_identifiers import TaxIdentifierType, format_us_ssn
from tests.models import (
    SsnTaxPayer,
    UntaxedParty,
)
from tests.factories import (
    generate_tax_id,
)


def expected_mask(display: str) -> str:
    """Return the masked form of a tax identifier display string."""

    return "*" * (len(display) - 4) + display[-4:]


class TestTaxIdentifierMasking:
    """Test that tax identifier fields mask and unmask."""

    def test_normalizes_on_construction(self, ssn_tax_payer_factory: Callable[..., SsnTaxPayer]) -> None:
        """Test that a formatted US tax identifier is normalized when the model is built."""

        raw_tax_id = generate_tax_id(TaxIdentifierType.SSN)
        payer = ssn_tax_payer_factory(tax_id=format_us_ssn(raw_tax_id))

        assert payer.tax_id == raw_tax_id

    def test_masks_all_but_last_four(self, ssn_tax_payer_factory: Callable[..., SsnTaxPayer]) -> None:
        """Test that masking hides every character except the last four."""

        payer = ssn_tax_payer_factory()
        display = str(payer.tax_id)

        assert payer.to_masked().tax_id == expected_mask(display)

    def test_unmask_restores_original_value(self, ssn_tax_payer_factory: Callable[..., SsnTaxPayer]) -> None:
        """Test that unmasking restores the original identifier."""

        payer = ssn_tax_payer_factory()
        display = str(payer.tax_id)

        assert payer.to_masked().to_unmask().tax_id == display

    def test_masking_twice_preserves_original(
        self, ssn_tax_payer_factory: Callable[..., SsnTaxPayer]
    ) -> None:
        """Test that masking an already-masked model keeps the original recoverable."""

        payer = ssn_tax_payer_factory()
        display = str(payer.tax_id)
        masked_twice = payer.to_masked().to_masked()

        assert masked_twice.tax_id == expected_mask(display)
        assert masked_twice.to_unmask().tax_id == display

    def test_masking_is_a_noop_without_tax_fields(
        self, untaxed_party_factory: Callable[..., UntaxedParty]
    ) -> None:
        """Test that masking a model without tax identifier fields returns it unchanged."""

        party = untaxed_party_factory()

        assert party.to_masked() is party
