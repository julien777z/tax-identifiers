from collections.abc import Callable

import pytest
from pydantic import ValidationError

from tax_validation import (
    BaseModel,
    ComparableUsTaxIdentifier,
    NormalizedString,
    StringBool,
    TaxIdentifierOrigin,
    TaxIdentifierType,
    TaxIdField,
    USState,
    USStateField,
    format_us_ssn,
)


def is_affirmative(value: str) -> bool:
    """Return whether a string token is an affirmative answer."""

    return value.strip().upper() in {"YES", "Y", "TRUE"}


class NormalizedHolder(BaseModel):
    """Test model with an uppercase-normalized string field."""

    value: NormalizedString(normalize_to_uppercase=True)


class ConsentHolder(BaseModel):
    """Test model with a string-backed boolean field."""

    consented: StringBool(predicate=is_affirmative)


class StateHolder(BaseModel):
    """Test model with a US state field."""

    state: USStateField


class UsTaxIdHolder(BaseModel):
    """Test model with a US tax identifier field."""

    tax_id: TaxIdField(origin=TaxIdentifierOrigin.US_TIN)


class MaskedTaxIdHolder(BaseModel):
    """Test model accepting a masked US tax identifier."""

    tax_id: TaxIdField(origin=TaxIdentifierOrigin.US_TIN, allow_masked=True)


class TestNormalizedString:
    """Tests for the configurable string normalizer field."""

    def test_uppercases_and_collapses_whitespace(self) -> None:
        """Test that the value is uppercased and internal whitespace is collapsed."""

        holder = NormalizedHolder(value="  acme   llc ")

        assert holder.value == "ACME LLC"


class TestStringBool:
    """Tests for the predicate-backed boolean field."""

    @pytest.mark.parametrize(
        ("value", "expected"),
        [("yes", True), ("no", False), (True, True)],
        ids=["affirmative", "negative", "bool_passthrough"],
    )
    def test_converts_via_predicate(self, value: bool | str, expected: bool) -> None:
        """Test that string inputs are converted through the predicate."""

        holder = ConsentHolder(consented=value)

        assert holder.consented is expected


class TestUSStateField:
    """Tests for US state coercion."""

    @pytest.mark.parametrize(
        ("value", "expected"),
        [("ca", USState.CALIFORNIA), ("New Hampshire", USState.NEW_HAMPSHIRE)],
        ids=["code", "name"],
    )
    def test_coerces_codes_and_names(self, value: str, expected: USState) -> None:
        """Test that postal codes and full names coerce to the enum."""

        holder = StateHolder(state=value)

        assert holder.state == expected

    def test_rejects_unknown_state(self) -> None:
        """Test that an unknown state raises a validation error."""

        with pytest.raises(ValidationError):
            StateHolder(state="Atlantis")


class TestTaxIdField:
    """Tests for the tax identifier field annotation."""

    def test_normalizes_us_identifier(self, tax_id_factory: Callable[..., str]) -> None:
        """Test that a US identifier is stored as a formatting-insensitive value."""

        raw_tax_id = tax_id_factory(TaxIdentifierType.SSN)
        holder = UsTaxIdHolder(tax_id=format_us_ssn(raw_tax_id))

        assert isinstance(holder.tax_id, ComparableUsTaxIdentifier)
        assert holder.tax_id == raw_tax_id

    def test_rejects_mask_characters_by_default(self) -> None:
        """Test that masked input is rejected unless masking is allowed."""

        with pytest.raises(ValidationError):
            UsTaxIdHolder(tax_id="*****6789")

    def test_allows_mask_characters_when_configured(self) -> None:
        """Test that masked input passes through when masking is allowed."""

        holder = MaskedTaxIdHolder(tax_id="*****6789")

        assert holder.tax_id == "*****6789"
