from collections.abc import Callable
from typing import Annotated, Final, assert_type

import tax_identifiers
from tax_identifiers import (
    Country,
    TaxIdFieldOptions,
    TaxIdStr,
    TaxIdentifierType,
)
from tax_identifiers.base import BaseModel
from tax_identifiers.fields import StrRequired
from tax_identifiers.us.enums import USState
from tests.conftest import (
    MaskableTaxIdFieldHolder,
    StateHolder,
    TaxIdentifierHolder,
    TaxIdFieldHolder,
)

COVERED_FIELD_TYPES: Final[frozenset[str]] = frozenset(
    {
        "SSNTaxIdField",
        "LenientSSNTaxIdField",
        "USTaxIdField",
        "ForeignTaxIdField",
        "UnknownTaxIdField",
        "TaxIdStr",
    }
)

FrenchTinField = Annotated[
    TaxIdStr,
    TaxIdFieldOptions(country=Country.FR, tax_id_type=TaxIdentifierType.FOREIGN_TIN),
]


class UnconfiguredStringHolder(BaseModel):
    """Model annotated with the shipped string field types that carry no tax configuration."""

    required: StrRequired
    tax_id: TaxIdStr


class CustomAnnotationHolder(BaseModel):
    """Model annotated with a caller-built annotation rather than a shipped alias."""

    tax_id: FrenchTinField


class TestStaticAnnotations:
    """Test that every shipped field type is usable and correctly typed in annotation position."""

    def test_aliases_resolve_to_their_underlying_types(
        self, tax_id_field_holder_factory: Callable[..., TaxIdFieldHolder]
    ) -> None:
        """Test that each alias resolves to its underlying type rather than to Any."""

        holder = tax_id_field_holder_factory()

        assert_type(holder.ssn, str)
        assert_type(holder.unknown, str)
        assert_type(UnconfiguredStringHolder(required="x", tax_id="x").tax_id, str)
        assert_type(StateHolder(state=USState.CALIFORNIA).state, USState)

    def test_mixin_combination_is_correctly_typed(
        self, tax_identifier_holder_factory: Callable[..., TaxIdentifierHolder]
    ) -> None:
        """Test that combining the masking mixin with a model keeps the field's declared type."""

        holder = tax_identifier_holder_factory()

        assert_type(holder.tax_id, str)
        assert_type(holder.to_masked().tax_id, str)

    def test_maskable_aliases_accept_masked_input(
        self,
        masked_tax_id_factory: Callable[..., str],
        maskable_tax_id_field_holder_factory: Callable[..., MaskableTaxIdFieldHolder],
    ) -> None:
        """Test that the mask-accepting aliases validate an already-masked value."""

        masked = masked_tax_id_factory()

        assert maskable_tax_id_field_holder_factory(us=masked).us == masked

    def test_every_shipped_field_type_is_covered(self) -> None:
        """Test that no exported field type is missing from this module."""

        exported = {
            name for name in tax_identifiers.__all__ if name.endswith("Field") or name == "TaxIdStr"
        }

        assert exported == COVERED_FIELD_TYPES
