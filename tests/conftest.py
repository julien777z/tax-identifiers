import random
from collections.abc import Callable
from typing import Final

import pytest

from tax_identifiers import (
    Country,
    ForeignTaxIdField,
    LenientSSNTaxIdField,
    MaskableForeignTaxIdField,
    MaskableUnknownTaxIdField,
    MaskableUSTaxIdField,
    SSNTaxIdField,
    TaxIdentifier,
    TaxIdentifierPairMixin,
    TaxIdentifierType,
    TaxValidator,
    USTaxIdField,
    UnknownTaxIdField,
    mask_tax_id,
)
from tax_identifiers.base import BaseModel
from tax_identifiers.us import metadata as us_metadata
from tax_identifiers.us.enums import USState
from tax_identifiers.us.fields import USStateField
from tax_identifiers.us.metadata import SSNAllocationEntry

FOREIGN_TAX_ID_PREFIX: Final[str] = "GB"
GIVEN_NAMES: Final[tuple[str, ...]] = ("Avery", "Jordan", "Riley", "Sasha")
FAMILY_NAMES: Final[tuple[str, ...]] = ("Alderton", "Brightwell", "Calloway", "Danforth")


class TaxIdentifierHolder(TaxIdentifierPairMixin, BaseModel):
    """Test model pairing the masking mixin with an SSN field."""

    tax_id: SSNTaxIdField


class LenientTaxIdentifierHolder(TaxIdentifierPairMixin, BaseModel):
    """Test model pairing the masking mixin with a lenient SSN field."""

    tax_id: LenientSSNTaxIdField


class PlainHolder(TaxIdentifierPairMixin, BaseModel):
    """Test model with the mixin but no tax identifier fields."""

    name: str


class TaxIdFieldHolder(BaseModel):
    """Test model annotated with every shipped tax identifier alias."""

    ssn: SSNTaxIdField
    lenient_ssn: LenientSSNTaxIdField
    us: USTaxIdField
    foreign: ForeignTaxIdField
    unknown: UnknownTaxIdField


class MaskableTaxIdFieldHolder(BaseModel):
    """Test model annotated with every shipped mask-accepting tax identifier alias."""

    us: MaskableUSTaxIdField
    foreign: MaskableForeignTaxIdField
    unknown: MaskableUnknownTaxIdField


class StateHolder(BaseModel):
    """Test model with a US state field."""

    state: USStateField


class CountryHolder(BaseModel):
    """Test model exposing a country field for coercion tests."""

    country: Country


class AllocatedSsn(BaseModel):
    """A structurally valid SSN paired with the allocation metadata it resolves to."""

    tax_id: str
    issued_state: USState
    issued_years: str


@pytest.fixture
def us_validator() -> TaxValidator:
    """Provide a US tax identifier validator."""

    return TaxValidator(Country.US)


@pytest.fixture
def tax_id_factory() -> Callable[..., str]:
    """Build random, structurally valid tax identifiers for the requested type."""

    def _build(
        tax_id_type: TaxIdentifierType = TaxIdentifierType.SSN,
        *,
        area: str | None = None,
        group: str | None = None,
        serial: str | None = None,
    ) -> str:
        if tax_id_type == TaxIdentifierType.FOREIGN_TIN:
            return f"{FOREIGN_TAX_ID_PREFIX}{random.randint(0, 99_999_999):08d}"

        resolved_area = area or f"{random.choice([*range(1, 666), *range(667, 900)]):03d}"
        resolved_group = group or f"{random.randint(1, 99):02d}"
        resolved_serial = serial or f"{random.randint(1, 9999):04d}"

        return f"{resolved_area}{resolved_group}{resolved_serial}"

    return _build


@pytest.fixture
def masked_tax_id_factory(tax_id_factory: Callable[..., str]) -> Callable[..., str]:
    """Build masked tax identifiers, optionally as a plain string from a serialized payload."""

    def _build(*, plain: bool = False) -> str:
        masked = mask_tax_id(tax_id_factory(TaxIdentifierType.SSN))

        return str(masked) if plain else masked

    return _build


@pytest.fixture
def full_name_factory() -> Callable[..., str]:
    """Build person names for tests that need one."""

    def _build() -> str:
        return f"{random.choice(GIVEN_NAMES)} {random.choice(FAMILY_NAMES)}"

    return _build


@pytest.fixture
def business_name_factory() -> Callable[..., str]:
    """Build business names for tests that need one."""

    def _build() -> str:
        return f"{random.choice(FAMILY_NAMES)} Holdings"

    return _build


@pytest.fixture
def normalizable_foreign_tax_id() -> tuple[str, str]:
    """Provide a raw foreign tax identifier paired with its normalized form."""

    raw = f" {FOREIGN_TAX_ID_PREFIX.lower()}-12 ab "

    return raw, raw.strip().upper()


@pytest.fixture
def tax_identifier_factory(
    tax_id_factory: Callable[..., str],
) -> Callable[..., TaxIdentifier]:
    """Build TaxIdentifier instances with generated, type-appropriate identifiers."""

    def _build(
        tax_id_type: TaxIdentifierType = TaxIdentifierType.SSN,
        tax_id: str | None = None,
        country: Country = Country.US,
    ) -> TaxIdentifier:
        resolved_tax_id = tax_id if tax_id is not None else tax_id_factory(tax_id_type)

        return TaxIdentifier(country=country, tax_id_type=tax_id_type, tax_id=resolved_tax_id)

    return _build


@pytest.fixture
def tax_identifier_holder_factory(
    tax_id_factory: Callable[..., str],
) -> Callable[..., TaxIdentifierHolder]:
    """Build TaxIdentifierHolder instances with a generated SSN."""

    def _build(**overrides: str) -> TaxIdentifierHolder:
        return TaxIdentifierHolder(**{"tax_id": tax_id_factory(TaxIdentifierType.SSN), **overrides})

    return _build


@pytest.fixture
def tax_id_field_holder_factory(
    tax_id_factory: Callable[..., str],
) -> Callable[..., TaxIdFieldHolder]:
    """Build TaxIdFieldHolder instances with a valid value in every aliased field."""

    def _build(**overrides: object) -> TaxIdFieldHolder:
        tax_id = tax_id_factory(TaxIdentifierType.SSN)
        defaults: dict[str, object] = {
            "ssn": tax_id,
            "lenient_ssn": tax_id,
            "us": tax_id,
            "foreign": tax_id_factory(TaxIdentifierType.FOREIGN_TIN),
            "unknown": tax_id,
        }

        return TaxIdFieldHolder.model_validate({**defaults, **overrides})

    return _build


@pytest.fixture
def maskable_tax_id_field_holder_factory(
    masked_tax_id_factory: Callable[..., str],
) -> Callable[..., MaskableTaxIdFieldHolder]:
    """Build MaskableTaxIdFieldHolder instances with a masked value in every aliased field."""

    def _build(**overrides: object) -> MaskableTaxIdFieldHolder:
        masked = masked_tax_id_factory()
        defaults: dict[str, object] = {"us": masked, "foreign": masked, "unknown": masked}

        return MaskableTaxIdFieldHolder.model_validate({**defaults, **overrides})

    return _build


@pytest.fixture
def ssn_allocation(monkeypatch: pytest.MonkeyPatch) -> dict[str, SSNAllocationEntry]:
    """Stub the SSN allocation dataset with known sample entries."""

    dataset: dict[str, SSNAllocationEntry] = {
        "212": {"state": USState.MARYLAND.value, "groups": {"01": "1936-1950"}},
        "100": {"state": USState.NEW_YORK.value, "groups": {"12": "1977-1978"}},
    }
    monkeypatch.setattr(us_metadata, "get_ssn_allocation_data", lambda: dataset)

    return dataset


@pytest.fixture
def allocated_ssn(ssn_allocation: dict[str, SSNAllocationEntry]) -> AllocatedSsn:
    """Provide a valid SSN for a known allocation entry with its expected metadata."""

    area = next(iter(ssn_allocation))
    entry = ssn_allocation[area]
    group, years = next(iter(entry["groups"].items()))

    return AllocatedSsn(
        tax_id=f"{area}{group}0001",
        issued_state=USState(entry["state"]),
        issued_years=years,
    )
