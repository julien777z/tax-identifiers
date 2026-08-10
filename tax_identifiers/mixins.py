from typing import TYPE_CHECKING, Self

from pydantic_super_model import SuperModelPydanticMixin

from tax_identifiers.annotations import TaxIdFieldOptions
from tax_identifiers.masking import mask_tax_id

if TYPE_CHECKING:
    MixinHost = SuperModelPydanticMixin
else:
    MixinHost = object


class TaxIdentifierPairMixin(MixinHost):
    """Normalize and mask tax identifier fields using tax-id annotation metadata."""

    def tax_id_field_options(self, field_name: str) -> TaxIdFieldOptions | None:
        """Return the country and type a tax identifier field declares, when it declares any."""

        field_info = self.get_annotated_fields(TaxIdFieldOptions).get(field_name)

        if field_info is None:
            return None

        return next(
            (metadata for metadata in field_info.matched_metadata if isinstance(metadata, TaxIdFieldOptions)),
            None,
        )

    def to_masked(self) -> Self:
        """Return a copy with tax-identifier fields masked and originals persisted."""

        if getattr(self, "_tax_identifiers_masked", False):
            return self

        masked_model = self.model_copy()
        tax_id_fields = masked_model.get_annotated_fields(TaxIdFieldOptions)
        has_update = False

        for field_name, field_info in tax_id_fields.items():
            value = field_info.value
            if not isinstance(value, str):
                continue

            object.__setattr__(masked_model, f"_original_{field_name}", value)

            masked_value = mask_tax_id(value)
            object.__setattr__(masked_model, field_name, masked_value)
            has_update = True

        if not has_update:
            return self

        object.__setattr__(masked_model, "_tax_identifiers_masked", True)

        return masked_model

    def to_unmask(self) -> Self:
        """Return a copy restored with original unmasked tax-identifier values."""

        unmasked_model = self.model_copy()
        tax_id_fields = unmasked_model.get_annotated_fields(TaxIdFieldOptions)
        has_update = False

        for field_name in tax_id_fields:
            original_value = getattr(unmasked_model, f"_original_{field_name}", None)

            if not isinstance(original_value, str):
                continue

            object.__setattr__(unmasked_model, field_name, original_value)
            has_update = True

        if not has_update:
            return self

        object.__setattr__(unmasked_model, "_tax_identifiers_masked", False)

        return unmasked_model
