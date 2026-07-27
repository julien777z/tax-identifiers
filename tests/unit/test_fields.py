from collections.abc import Callable
from typing import Annotated

import pytest
from pydantic import ValidationError

from tax_identifiers import (
    BaseModel,
    ComparableUsTaxIdentifier,
    Country,
    MaskableUSTaxIdField,
    TaxIdentifierType,
    TaxIdFieldOptions,
    TaxIdStr,
    UnknownTaxIdField,
    USState,
    USStateField,
    USTaxIdField,
    format_us_ssn,
    is_masked_tax_id,
    mask_tax_id,
)


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

    def test_rejects_masked_value_by_default(self) -> None:
        """Test that a masked tax identifier is rejected unless masking is allowed."""

        with pytest.raises(ValidationError, match="Tax ID cannot contain mask characters"):
            UsTaxIdHolder(tax_id=mask_tax_id("123456789"))

    def test_rejects_non_string_value(self) -> None:
        """Test that a non-string tax identifier is rejected without a type error."""

        with pytest.raises(ValidationError):
            UsTaxIdHolder(tax_id=123456789)

    def test_accepts_masked_value_when_configured(self) -> None:
        """Test that a masked tax identifier passes through when masking is allowed."""

        masked = mask_tax_id("123456789")
        holder = MaskedTaxIdHolder(tax_id=masked)

        assert holder.tax_id == masked
        assert is_masked_tax_id(holder.tax_id)

    def test_accepts_plain_masked_string_when_configured(self) -> None:
        """Test that a plain masked string from a serialized payload is accepted."""

        holder = MaskedTaxIdHolder(tax_id="*****6789")

        assert holder.tax_id == "*****6789"
        assert is_masked_tax_id(holder.tax_id)


class TestUnknownCountryTaxIdField:
    """Tests for the country-agnostic (unknown) tax identifier field."""

    def test_normalizes_generically(self) -> None:
        """Test that an unknown-country field uppercases without US cleaning."""

        holder = UnknownTaxIdHolder(tax_id="  fr-12 ab ")

        assert holder.tax_id == "FR-12 AB"


class TestInlineTaxIdFieldOptions:
    """Tests for configuring a tax identifier field inline instead of through a shipped alias."""

    def test_matches_the_equivalent_alias(self, tax_id_factory: Callable[..., str]) -> None:
        """Test that an inline annotation behaves identically to the matching alias."""

        formatted = format_us_ssn(tax_id_factory(TaxIdentifierType.SSN))

        inline = InlineUsTaxIdHolder(tax_id=formatted)
        aliased = UsTaxIdHolder(tax_id=formatted)

        assert inline.tax_id == aliased.tax_id
        assert type(inline.tax_id) is type(aliased.tax_id)


class TestMaskableOptions:
    """Tests for deriving mask-accepting options from a base annotation."""

    def test_maskable_preserves_country_and_type(self) -> None:
        """Test that the derived options keep the country and type and only allow masking."""

        options = TaxIdFieldOptions(country=Country.US, tax_id_type=TaxIdentifierType.SSN)
        maskable = options.maskable

        assert (maskable.country, maskable.tax_id_type) == (options.country, options.tax_id_type)
        assert maskable.allow_masked
        assert not options.allow_masked
