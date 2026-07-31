from typing import Annotated

from tax_identifiers import (
    AllowMasked,
    Country,
    ForeignTaxIdField,
    LenientSSNTaxIdField,
    SSNTaxIdField,
    TaxIdentifierPairMixin,
    USTaxIdField,
    UnknownTaxIdField,
)
from tax_identifiers.base import BaseModel
from tax_identifiers.us.enums import USState
from tax_identifiers.us.fields import USStateField


class SsnTaxPayer(TaxIdentifierPairMixin, BaseModel):
    """Test model pairing the masking mixin with an SSN field."""

    tax_id: SSNTaxIdField


class LenientSsnTaxPayer(TaxIdentifierPairMixin, BaseModel):
    """Test model pairing the masking mixin with a lenient SSN field."""

    tax_id: LenientSSNTaxIdField


class UntaxedParty(TaxIdentifierPairMixin, BaseModel):
    """Test model with the mixin but no tax identifier fields."""

    name: str


class TaxIdAliasSet(BaseModel):
    """Test model annotated with every shipped tax identifier alias."""

    ssn: SSNTaxIdField
    lenient_ssn: LenientSSNTaxIdField
    us: USTaxIdField
    foreign: ForeignTaxIdField
    unknown: UnknownTaxIdField


class MaskedTaxIdAliasSet(BaseModel):
    """Test model annotated with every shipped alias accepting masked input."""

    us: Annotated[USTaxIdField, AllowMasked]
    foreign: Annotated[ForeignTaxIdField, AllowMasked]
    unknown: Annotated[UnknownTaxIdField, AllowMasked]


class StateRecord(BaseModel):
    """Test model with a US state field."""

    state: USStateField


class CountryRecord(BaseModel):
    """Test model exposing a country field for coercion tests."""

    country: Country


class AllocatedSsn(BaseModel):
    """A structurally valid SSN paired with the allocation metadata it resolves to."""

    tax_id: str
    issued_state: USState
    issued_years: str
