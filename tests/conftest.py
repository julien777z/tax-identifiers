import random
from collections.abc import Callable
from typing import Annotated, Final

import pytest

from tax_identifiers import (
    BaseModel,
    Country,
    MaskableUSTaxIdField,
    SSNTaxIdField,
    TaxIdentifier,
    TaxIdentifierPairMixin,
    TaxIdentifierType,
    TaxIdStr,
    TaxIdFieldOptions,
    TaxValidator,
    UnknownTaxIdField,
    USState,
    USStateField,
    USTaxIdField,
    mask_tax_id,
)
from tax_identifiers.us import metadata as us_metadata
from tax_identifiers.us.metadata import SSNAllocationEntry

FOREIGN_TAX_ID_PREFIX: Final[str] = "GB"
GIVEN_NAMES: Final[tuple[str, ...]] = ("Avery", "Jordan", "Riley", "Sasha")
FAMILY_NAMES: Final[tuple[str, ...]] = ("Alderton", "Brightwell", "Calloway", "Danforth")


class TaxIdentifierHolder(TaxIdentifierPairMixin, BaseModel):
    """Test model exposing a single maskable US tax identifier field."""

    tax_id: SSNTaxIdField


class PlainHolder(TaxIdentifierPairMixin, BaseModel):
    """Test model with the mixin but no tax identifier fields."""

    name: str


class StateHolder(BaseModel):
    """Test model with a US state field."""

    state: USStateField


class UsTaxIdHolder(BaseModel):
    """Test model with a US tax identifier field."""

    tax_id: USTaxIdField


class MaskedTaxIdHolder(BaseModel):
    """Test model accepting a masked US tax identifier."""

    tax_id: MaskableUSTaxIdField


class UnknownTaxIdHolder(BaseModel):
    """Test model with a country-agnostic tax identifier field."""

    tax_id: UnknownTaxIdField


class InlineUsTaxIdHolder(BaseModel):
    """Test model configuring a US tax identifier field inline rather than through an alias."""

    tax_id: Annotated[TaxIdStr, TaxIdFieldOptions(country=Country.US)]


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

    def _build(*, lowercase: bool = False) -> str:
        name = f"{random.choice(GIVEN_NAMES)} {random.choice(FAMILY_NAMES)}"

        return name.lower() if lowercase else name

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
def unallocated_ssn(
    ssn_allocation: dict[str, SSNAllocationEntry], tax_id_factory: Callable[..., str]
) -> str:
    """Provide a structurally valid SSN whose area is absent from the allocation dataset."""

    area = next(
        f"{candidate:03d}"
        for candidate in range(1, 900)
        if f"{candidate:03d}" not in ssn_allocation
    )

    return tax_id_factory(TaxIdentifierType.SSN, area=area)


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
