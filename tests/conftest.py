from collections.abc import Callable

import pytest

from tax_identifiers import Country, TaxIdentifier, TaxValidator
from tax_identifiers.us import metadata as us_metadata
from tax_identifiers.us.enums import USState
from tax_identifiers.us.metadata import SSNAllocationEntry
from tests.factories import (
    FOREIGN_TAX_ID_PREFIX,
    LenientSsnTaxPayerFactory,
    MaskedTaxIdAliasSetFactory,
    SsnTaxPayerFactory,
    TaxIdAliasSetFactory,
    TaxIdentifierFactory,
    UntaxedPartyFactory,
)
from tests.models import (
    AllocatedSsn,
    LenientSsnTaxPayer,
    MaskedTaxIdAliasSet,
    SsnTaxPayer,
    TaxIdAliasSet,
    UntaxedParty,
)


@pytest.fixture
def us_validator() -> TaxValidator:
    """Provide a US tax identifier validator."""

    return TaxValidator(Country.US)


@pytest.fixture
def normalizable_foreign_tax_id() -> tuple[str, str]:
    """Provide a raw foreign tax identifier paired with its normalized form."""

    raw = f" {FOREIGN_TAX_ID_PREFIX.lower()}-12 ab "

    return raw, raw.strip().upper()


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


@pytest.fixture
def tax_identifier_factory() -> Callable[..., TaxIdentifier]:
    """Build TaxIdentifier models."""

    return TaxIdentifierFactory.build


@pytest.fixture
def ssn_tax_payer_factory() -> Callable[..., SsnTaxPayer]:
    """Build tax payers whose SSN field asserts validity."""

    return SsnTaxPayerFactory.build


@pytest.fixture
def lenient_ssn_tax_payer_factory() -> Callable[..., LenientSsnTaxPayer]:
    """Build tax payers whose SSN field accepts reserved ranges."""

    return LenientSsnTaxPayerFactory.build


@pytest.fixture
def untaxed_party_factory() -> Callable[..., UntaxedParty]:
    """Build parties that carry the masking mixin but no tax identifier."""

    return UntaxedPartyFactory.build


@pytest.fixture
def tax_id_alias_set_factory() -> Callable[..., TaxIdAliasSet]:
    """Build models carrying one field per shipped alias."""

    return TaxIdAliasSetFactory.build


@pytest.fixture
def masked_tax_id_alias_set_factory() -> Callable[..., MaskedTaxIdAliasSet]:
    """Build models whose alias fields accept an already-masked value."""

    return MaskedTaxIdAliasSetFactory.build
