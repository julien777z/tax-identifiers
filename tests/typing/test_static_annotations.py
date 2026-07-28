from collections.abc import Callable
from typing import Annotated, Final, assert_type

import tax_identifiers
from tax_identifiers import (
    Country,
    ForeignTaxIdField,
    MaskableForeignTaxIdField,
    MaskableUSTaxIdField,
    MaskableUnknownTaxIdField,
    LenientSSNTaxIdField,
    SSNTaxIdField,
    TaxIdFieldOptions,
    TaxIdStr,
    TaxIdentifierType,
    USTaxIdField,
    UnknownTaxIdField,
)
from tax_identifiers.base import BaseModel
from tax_identifiers.fields import StrRequired
from tax_identifiers.us.enums import USState
from tax_identifiers.us.fields import USStateField
from tests.conftest import TaxIdentifierHolder

COVERED_FIELD_TYPES: Final[frozenset[str]] = frozenset(
    {
        "SSNTaxIdField",
        "LenientSSNTaxIdField",
        "USTaxIdField",
        "ForeignTaxIdField",
        "UnknownTaxIdField",
        "MaskableUSTaxIdField",
        "MaskableForeignTaxIdField",
        "MaskableUnknownTaxIdField",
        "TaxIdStr",
    }
)

FrenchTinField = Annotated[
    TaxIdStr,
    TaxIdFieldOptions(country=Country.FR, tax_id_type=TaxIdentifierType.FOREIGN_TIN),
]


class TaxIdFieldHolder(BaseModel):
    """Model annotated with every shipped tax identifier alias."""

    ssn: SSNTaxIdField
    lenient_ssn: LenientSSNTaxIdField
    us: USTaxIdField
    foreign: ForeignTaxIdField
    unknown: UnknownTaxIdField


class MaskableTaxIdFieldHolder(BaseModel):
    """Model annotated with every shipped mask-accepting tax identifier alias."""

    us: MaskableUSTaxIdField
    foreign: MaskableForeignTaxIdField
    unknown: MaskableUnknownTaxIdField


class OtherFieldHolder(BaseModel):
    """Model annotated with the remaining shipped field types."""

    required: StrRequired
    state: USStateField
    tax_id: TaxIdStr


class CustomAnnotationHolder(BaseModel):
    """Model annotated with a caller-built annotation rather than a shipped alias."""

    tax_id: FrenchTinField


class TestStaticAnnotations:
    """Test that every shipped field type is usable and correctly typed in annotation position."""

    def test_aliases_resolve_to_their_underlying_types(
        self, tax_id_factory: Callable[..., str]
    ) -> None:
        """Test that each alias resolves to its underlying type rather than to Any."""

        raw_tax_id = tax_id_factory(TaxIdentifierType.SSN)
        holder = TaxIdFieldHolder(
            ssn=raw_tax_id,
            lenient_ssn=raw_tax_id,
            us=raw_tax_id,
            foreign=tax_id_factory(TaxIdentifierType.FOREIGN_TIN),
            unknown=raw_tax_id,
        )

        assert_type(holder.ssn, str)
        assert_type(holder.unknown, str)
        assert_type(
            OtherFieldHolder(required="x", state=USState.CALIFORNIA, tax_id="x").state, USState
        )

    def test_mixin_combination_is_correctly_typed(
        self, tax_identifier_holder_factory: Callable[..., TaxIdentifierHolder]
    ) -> None:
        """Test that combining the masking mixin with a model keeps the field's declared type."""

        holder = tax_identifier_holder_factory()

        assert_type(holder.tax_id, str)
        assert_type(holder.to_masked().tax_id, str)

    def test_maskable_aliases_accept_masked_input(
        self, masked_tax_id_factory: Callable[..., str]
    ) -> None:
        """Test that the mask-accepting aliases validate an already-masked value."""

        masked = masked_tax_id_factory()
        holder = MaskableTaxIdFieldHolder(us=masked, foreign=masked, unknown=masked)

        assert holder.us == masked

    def test_every_shipped_field_type_is_covered(self) -> None:
        """Test that no exported field type is missing from this module."""

        exported = {
            name
            for name in tax_identifiers.__all__
            if name.endswith(("Field", "TaxIdStr", "StrRequired"))
        }

        assert exported == COVERED_FIELD_TYPES
