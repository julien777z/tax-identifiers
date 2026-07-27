from typing import Annotated, assert_type

import tax_identifiers
from tax_identifiers import (
    BaseModel,
    Country,
    ForeignTaxIdField,
    MaskableForeignTaxIdField,
    MaskableUnknownTaxIdField,
    MaskableUSTaxIdField,
    SSNTaxIdField,
    StrRequired,
    TaxIdentifierPairMixin,
    TaxIdentifierType,
    TaxIdFieldOptions,
    TaxIdStr,
    UnknownTaxIdField,
    USState,
    USStateField,
    USTaxIdField,
)

FrenchTinField = Annotated[
    TaxIdStr,
    TaxIdFieldOptions(country=Country.FR, tax_id_type=TaxIdentifierType.FOREIGN_TIN),
]


class TaxIdFieldHolder(BaseModel):
    """Model annotated with every shipped tax identifier alias."""

    ssn: SSNTaxIdField
    us: USTaxIdField
    foreign: ForeignTaxIdField
    unknown: UnknownTaxIdField


class MaskableTaxIdFieldHolder(BaseModel):
    """Model annotated with every shipped mask-accepting tax identifier alias."""

    us: MaskableUSTaxIdField
    foreign: MaskableForeignTaxIdField
    unknown: MaskableUnknownTaxIdField


class MixinHolder(TaxIdentifierPairMixin, BaseModel):
    """Model combining the masking mixin with an aliased field."""

    tax_id: SSNTaxIdField


class OtherFieldHolder(BaseModel):
    """Model annotated with the remaining shipped field types."""

    required: StrRequired
    state: USStateField


class CustomAnnotationHolder(BaseModel):
    """Model annotated with a caller-built annotation rather than a shipped alias."""

    tax_id: FrenchTinField


def test_annotations_resolve_to_their_underlying_types() -> None:
    """Test that each alias resolves to its underlying type, not to Any."""

    holder = TaxIdFieldHolder(ssn="123-45-6789", us="123456789", foreign="gb-1234", unknown="ab-12")

    assert_type(holder.ssn, str)
    assert_type(holder.unknown, str)
    assert_type(OtherFieldHolder(required="x", state=USState.CALIFORNIA).state, USState)
    assert_type(MixinHolder(tax_id="123-45-6789").tax_id, str)


def test_every_shipped_field_type_is_covered() -> None:
    """Test that no exported field type is missing from this guard."""

    exported = {
        name
        for name in tax_identifiers.__all__
        if name.endswith(("Field", "TaxIdStr", "StrRequired"))
    }
    annotated = set(globals()) | {"TaxIdFieldOptions"}

    assert exported - annotated == set()
