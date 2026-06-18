from typing import Self

from pydantic import model_validator

from tax_validation.enums import TaxIdentifierOrigin, TinType
from tax_validation.normalization.fields import TaxIdFieldOptions
from tax_validation.normalization.tax_identifiers import ComparableUsTaxIdentifier
from tax_validation.normalization.transformers import transform_tax_identifier


def mask_tax_id(value: str) -> str:
    """Mask a tax ID, preserving the last 4 characters."""

    if len(value) <= 4:
        return "*" * len(value)

    return "*" * (len(value) - 4) + value[-4:]


class TaxIdentifierPairMixin:
    """Normalize and mask tax identifier fields using tax-id annotation metadata."""

    @model_validator(mode="after")
    def normalize_tax_identifier_fields_if_present(self) -> Self:
        """Normalize tax identifier fields and wrap strict US identifiers for comparison."""

        if getattr(self, "_tax_identifiers_masked", False):
            return self

        tax_id_fields = self.get_annotated_fields(TaxIdFieldOptions)

        for field_name in tax_id_fields:
            options = self.tax_id_field_options(field_name)
            if options is None:
                continue

            value = getattr(self, field_name, None)
            if not isinstance(value, str):
                continue

            if "*" in value and options.allow_masked:
                continue

            normalized_tax_identifier = transform_tax_identifier(
                value,
                origin=options.origin,
                tin_type=options.tin_type,
            )

            if options.origin == TaxIdentifierOrigin.US_TIN and normalized_tax_identifier:
                object.__setattr__(self, field_name, ComparableUsTaxIdentifier(value))

        return self

    def tax_id_field_options(self, field_name: str) -> TaxIdFieldOptions | None:
        """Return tax-id field metadata when present."""

        tax_id_fields = self.get_annotated_fields(TaxIdFieldOptions)
        field_info = tax_id_fields.get(field_name)

        if field_info is None:
            return None

        matched_metadata = getattr(field_info, "matched_metadata", None)
        if matched_metadata is None:
            model_field = type(self).model_fields.get(field_name)
            matched_metadata = model_field.metadata if model_field else ()

        if not matched_metadata:
            return None

        return next(
            (metadata for metadata in matched_metadata if isinstance(metadata, TaxIdFieldOptions)),
            None,
        )

    @property
    def tax_identifier_origin(self) -> TaxIdentifierOrigin:
        """Return tax-id origin metadata for the tax_id field."""

        options = self.tax_id_field_options("tax_id")

        return options.origin if options else TaxIdentifierOrigin.US_TIN

    @property
    def tin_type(self) -> TinType | None:
        """Return optional tin type metadata for the tax_id field."""

        options = self.tax_id_field_options("tax_id")

        return options.tin_type if options else None

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
