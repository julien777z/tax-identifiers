import random
from collections.abc import Callable

import pytest

from tax_validation import (
    BaseModel,
    TaxIdentifierModel,
    TaxIdentifierOrigin,
    TaxIdentifierPairMixin,
    TaxIdentifierType,
    TaxIdField,
    TinType,
    USState,
    USTaxValidator,
)
from tax_validation.us import models as us_models
from tax_validation.us.models import SSNAllocationEntry

FOREIGN_TAX_ID_PREFIX = "GB"


class TaxIdentifierHolder(TaxIdentifierPairMixin, BaseModel):
    """Test model exposing a single maskable US tax identifier field."""

    tax_id: TaxIdField(origin=TaxIdentifierOrigin.US_TIN, tin_type=TinType.SSN)


@pytest.fixture
def us_validator() -> USTaxValidator:
    """Provide a US tax identifier validator."""

    return USTaxValidator()


@pytest.fixture
def tax_id_factory() -> Callable[..., str]:
    """Build random, structurally valid tax identifiers for the requested type."""

    def _build(tax_id_type: TaxIdentifierType = TaxIdentifierType.SSN) -> str:
        if tax_id_type == TaxIdentifierType.FOREIGN_TIN:
            return f"{FOREIGN_TAX_ID_PREFIX}{random.randint(0, 99_999_999):08d}"

        area = random.choice([*range(1, 666), *range(667, 900)])
        group = random.randint(1, 99)
        serial = random.randint(1, 9999)

        return f"{area:03d}{group:02d}{serial:04d}"

    return _build


@pytest.fixture
def tax_identifier_model_factory(
    tax_id_factory: Callable[..., str],
) -> Callable[..., TaxIdentifierModel]:
    """Build TaxIdentifierModel instances with generated, type-appropriate identifiers."""

    def _build(
        tax_id_type: TaxIdentifierType = TaxIdentifierType.SSN,
        tax_id: str | None = None,
    ) -> TaxIdentifierModel:
        resolved_tax_id = tax_id if tax_id is not None else tax_id_factory(tax_id_type)

        return TaxIdentifierModel(tax_id_type=tax_id_type, tax_id=resolved_tax_id)

    return _build


@pytest.fixture
def tax_identifier_holder_factory(
    tax_id_factory: Callable[..., str],
) -> Callable[..., TaxIdentifierHolder]:
    """Build TaxIdentifierHolder instances with a generated SSN."""

    def _build(**overrides) -> TaxIdentifierHolder:
        return TaxIdentifierHolder(**{"tax_id": tax_id_factory(TaxIdentifierType.SSN), **overrides})

    return _build


@pytest.fixture
def ssn_allocation(monkeypatch: pytest.MonkeyPatch) -> dict[str, SSNAllocationEntry]:
    """Stub the SSN allocation dataset with known sample entries."""

    dataset: dict[str, SSNAllocationEntry] = {
        "212": {"state": USState.MARYLAND.value, "groups": {"01": "1936-1950"}},
        "100": {"state": USState.NEW_YORK.value, "groups": {"12": "1977-1978"}},
    }
    monkeypatch.setattr(us_models, "SSN_ALLOCATION_DATA", dataset)

    return dataset
