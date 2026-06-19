from collections.abc import Callable

from tax_validation import (
    BaseModel,
    Country,
    TaxIdentifierPairMixin,
    TaxIdentifierType,
    format_us_ssn,
)
from tests.conftest import TaxIdentifierHolder


def expected_mask(display: str) -> str:
    """Return the masked form of a tax identifier display string."""

    return "*" * (len(display) - 4) + display[-4:]


class PlainHolder(TaxIdentifierPairMixin, BaseModel):
    """Test model with the mixin but no tax identifier fields."""

    name: str


class TestTaxIdentifierMasking:
    """Tests for masking and unmasking tax identifier fields."""

    def test_normalizes_on_construction(
        self,
        tax_identifier_holder_factory: Callable[..., TaxIdentifierHolder],
        tax_id_factory: Callable[..., str],
    ) -> None:
        """Test that a formatted US tax identifier is normalized when the model is built."""

        raw_tax_id = tax_id_factory(TaxIdentifierType.SSN)
        holder = tax_identifier_holder_factory(tax_id=format_us_ssn(raw_tax_id))

        assert holder.tax_id == raw_tax_id

    def test_masks_all_but_last_four(
        self,
        tax_identifier_holder_factory: Callable[..., TaxIdentifierHolder],
    ) -> None:
        """Test that masking hides every character except the last four."""

        holder = tax_identifier_holder_factory()
        display = str(holder.tax_id)

        assert holder.to_masked().tax_id == expected_mask(display)

    def test_unmask_restores_original_value(
        self,
        tax_identifier_holder_factory: Callable[..., TaxIdentifierHolder],
    ) -> None:
        """Test that unmasking restores the original identifier."""

        holder = tax_identifier_holder_factory()
        display = str(holder.tax_id)

        assert holder.to_masked().to_unmask().tax_id == display

    def test_masking_twice_preserves_original(
        self,
        tax_identifier_holder_factory: Callable[..., TaxIdentifierHolder],
    ) -> None:
        """Test that masking an already-masked model keeps the original recoverable."""

        holder = tax_identifier_holder_factory()
        display = str(holder.tax_id)
        masked_twice = holder.to_masked().to_masked()

        assert masked_twice.tax_id == expected_mask(display)
        assert masked_twice.to_unmask().tax_id == display

    def test_masking_is_a_noop_without_tax_fields(self) -> None:
        """Test that masking a model without tax identifier fields returns it unchanged."""

        holder = PlainHolder(name="Acme")

        assert holder.to_masked() is holder


class TestTaxIdentifierFieldMetadata:
    """Tests for tax identifier annotation metadata accessors."""

    def test_exposes_country_and_type(
        self,
        tax_identifier_holder_factory: Callable[..., TaxIdentifierHolder],
    ) -> None:
        """Test that the field's country and tax identifier type are exposed from metadata."""

        holder = tax_identifier_holder_factory()

        assert holder.tax_identifier_country == Country.US
        assert holder.tax_identifier_type == TaxIdentifierType.SSN
