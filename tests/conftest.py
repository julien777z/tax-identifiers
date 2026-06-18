from collections.abc import Callable

import pytest

from tax_validation import (
    BaseModel,
    TaxIdentifierOrigin,
    TaxIdentifierPairMixin,
    TaxIdField,
    TinType,
    USTaxValidator,
)

VALID_SSN = "123-45-6789"


class TaxIdentifierHolder(TaxIdentifierPairMixin, BaseModel):
    """Test model exposing a single maskable US tax identifier field."""

    tax_id: TaxIdField(origin=TaxIdentifierOrigin.US_TIN, tin_type=TinType.SSN)


@pytest.fixture
def us_validator() -> USTaxValidator:
    """Provide a US tax identifier validator."""

    return USTaxValidator()


@pytest.fixture
def tax_identifier_holder_factory() -> Callable[..., TaxIdentifierHolder]:
    """Build TaxIdentifierHolder instances with a default SSN."""

    def _build(**overrides) -> TaxIdentifierHolder:
        return TaxIdentifierHolder(**{"tax_id": VALID_SSN, **overrides})

    return _build
