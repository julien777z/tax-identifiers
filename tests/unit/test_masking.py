from collections.abc import Callable

from tax_validation import BaseModel, TaxIdentifierOrigin, TaxIdentifierPairMixin, TinType
from tests.conftest import TaxIdentifierHolder


class PlainHolder(TaxIdentifierPairMixin, BaseModel):
    """Test model with the mixin but no tax identifier fields."""

    name: str


class TestTaxIdentifierMasking:
    """Tests for masking and unmasking tax identifier fields."""

    def test_normalizes_on_construction(
        self,
        tax_identifier_holder_factory: Callable[..., TaxIdentifierHolder],
    ) -> None:
        """Test that a US tax identifier is normalized when the model is built."""

        holder = tax_identifier_holder_factory()

        assert holder.tax_id == "123456789"

    def test_masks_all_but_last_four(
        self,
        tax_identifier_holder_factory: Callable[..., TaxIdentifierHolder],
    ) -> None:
        """Test that masking hides every character except the last four."""

        masked = tax_identifier_holder_factory().to_masked()

        assert masked.tax_id == "*******6789"

    def test_unmask_restores_original_value(
        self,
        tax_identifier_holder_factory: Callable[..., TaxIdentifierHolder],
    ) -> None:
        """Test that unmasking restores the original identifier."""

        holder = tax_identifier_holder_factory()
        restored = holder.to_masked().to_unmask()

        assert restored.tax_id == "123456789"

    def test_masking_twice_preserves_original(
        self,
        tax_identifier_holder_factory: Callable[..., TaxIdentifierHolder],
    ) -> None:
        """Test that masking an already-masked model keeps the original recoverable."""

        masked_twice = tax_identifier_holder_factory().to_masked().to_masked()

        assert masked_twice.tax_id == "*******6789"
        assert masked_twice.to_unmask().tax_id == "123456789"

    def test_masking_is_a_noop_without_tax_fields(self) -> None:
        """Test that masking a model without tax identifier fields returns it unchanged."""

        holder = PlainHolder(name="Acme")

        assert holder.to_masked() is holder


class TestTaxIdentifierMetadata:
    """Tests for tax identifier annotation metadata accessors."""

    def test_exposes_origin_and_tin_type(
        self,
        tax_identifier_holder_factory: Callable[..., TaxIdentifierHolder],
    ) -> None:
        """Test that the field's origin and tin type are exposed from metadata."""

        holder = tax_identifier_holder_factory()

        assert holder.tax_identifier_origin == TaxIdentifierOrigin.US_TIN
        assert holder.tin_type == TinType.SSN
