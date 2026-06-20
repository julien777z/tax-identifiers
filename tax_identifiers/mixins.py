from typing import Self

from pydantic import model_validator

from tax_identifiers.countries import Country
from tax_identifiers.enums import TaxIdentifierType
from tax_identifiers.fields import TaxIdFieldOptions
from tax_identifiers.rules import get_country_rules


def mask_tax_id(value: str) -> str:
    """Mask a tax ID, preserving the last 4 characters."""

    if len(value) <= 4:
        return "*" * len(value)

    return "*" * (len(value) - 4) + value[-4:]


class TaxIdentifierPairMixin:
    """Normalize and mask tax identifier fields using tax-id annotation metadata."""

    @model_validator(mode="after")
    def normalize_tax_identifier_fields_if_present(self) -> Self:
        """Normalize tax identifier fields using each field's country rules."""

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

            normalized = get_country_rules(options.country).normalize(value, options.tax_id_type)
            object.__setattr__(self, field_name, normalized)

        return self

    def tax_id_field_options(self, field_name: str) -> TaxIdFieldOptions | None:
        """Return tax-id field metadata when present."""

        field_info = self.get_annotated_fields(TaxIdFieldOptions).get(field_name)

        if field_info is None:
            return None

        return next(
            (
                metadata
                for metadata in field_info.matched_metadata
                if isinstance(metadata, TaxIdFieldOptions)
            ),
            None,
        )

    @property
    def tax_identifier_country(self) -> Country | None:
        """Return the country metadata for the tax_id field."""

        options = self.tax_id_field_options("tax_id")

        return options.country if options else None

    @property
    def tax_identifier_type(self) -> TaxIdentifierType | None:
        """Return the tax identifier type metadata for the tax_id field."""

        options = self.tax_id_field_options("tax_id")

        return options.tax_id_type if options else None

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
