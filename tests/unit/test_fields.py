from collections.abc import Callable
from typing import Annotated

import pytest
from pydantic import ValidationError

from tax_identifiers import (
    BaseModel,
    ComparableUsTaxIdentifier,
    Country,
    MaskableUSTaxIdField,
    NormalizedStringOptions,
    SSNTaxIdField,
    StringBoolOptions,
    TaxIdentifierPairMixin,
    TaxIdentifierType,
    TaxIdFieldOptions,
    UnknownTaxIdField,
    UppercaseString,
    USState,
    USStateField,
    USTaxIdField,
    format_us_ssn,
    is_masked_tax_id,
    mask_tax_id,
)


def is_affirmative(value: str) -> bool:
    """Return whether a string token is an affirmative answer."""

    return value.strip().upper() in {"YES", "Y", "TRUE"}


class NormalizedHolder(BaseModel):
    """Test model with an uppercase-normalized string field."""

    value: UppercaseString


class ConsentHolder(BaseModel):
    """Test model with a string-backed boolean field."""

    consented: Annotated[bool, "string_bool", StringBoolOptions(predicate=is_affirmative)]


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

    tax_id: Annotated[
        str,
        "tax_id",
        TaxIdFieldOptions(country=Country.US, tax_id_type=TaxIdentifierType.US_UNSPECIFIED),
    ]


class AliasPairHolder(TaxIdentifierPairMixin, BaseModel):
    """Test model pairing the masking mixin with an aliased SSN field."""

    tax_id: SSNTaxIdField


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

    def test_normalizes_without_country_rules(self) -> None:
        """Test that the country-agnostic field applies no country-specific cleaning."""

        holder = UnknownTaxIdHolder(tax_id=" ab-12 ")

        assert holder.tax_id == "AB-12"


class TestInlineTaxIdFieldOptions:
    """Tests for configuring a tax identifier field inline instead of through a shipped alias."""

    def test_matches_the_equivalent_alias(self, tax_id_factory: Callable[..., str]) -> None:
        """Test that an inline annotation behaves identically to the matching alias."""

        raw_tax_id = tax_id_factory(TaxIdentifierType.SSN)
        formatted = format_us_ssn(raw_tax_id)

        inline = InlineUsTaxIdHolder(tax_id=formatted)
        aliased = UsTaxIdHolder(tax_id=formatted)

        assert inline.tax_id == aliased.tax_id
        assert type(inline.tax_id) is type(aliased.tax_id)

    def test_rejects_masked_value_by_default(self) -> None:
        """Test that an inline annotation rejects masked values like the alias does."""

        with pytest.raises(ValidationError, match="Tax ID cannot contain mask characters"):
            InlineUsTaxIdHolder(tax_id=mask_tax_id("123456789"))


class TestAliasedFieldMetadata:
    """Tests that annotation metadata stays discoverable through a module-level alias."""

    def test_mixin_resolves_options_through_alias(self) -> None:
        """Test that the masking mixin finds tax ID options behind an alias."""

        holder = AliasPairHolder(tax_id="123-45-6789")

        assert "tax_id" in holder.get_annotated_fields(TaxIdFieldOptions)
        assert holder.tax_identifier_country is Country.US
        assert holder.tax_identifier_type is TaxIdentifierType.SSN

    def test_masks_and_unmasks_through_alias(self) -> None:
        """Test that masking round-trips on a model annotated with an alias."""

        holder = AliasPairHolder(tax_id="123-45-6789")
        masked = holder.to_masked()

        assert masked.tax_id == "*******6789"
        assert masked.to_unmask().tax_id == "123-45-6789"

    def test_alias_instances_are_shared_safely(self) -> None:
        """Test that two models sharing one alias validate independently."""

        class FirstHolder(BaseModel):
            """Test model sharing the aliased US tax identifier field."""

            tax_id: USTaxIdField

        class SecondHolder(BaseModel):
            """Test model sharing the same aliased US tax identifier field."""

            tax_id: USTaxIdField

        assert FirstHolder(tax_id="123-45-6789").tax_id == SecondHolder(tax_id="123456789").tax_id


class TestNormalizedStringOptions:
    """Tests for the normalization options metadata class."""

    def test_rejects_conflicting_casing_flags(self) -> None:
        """Test that conflicting casing options raise when the annotation is built."""

        with pytest.raises(ValueError, match="Only one of"):
            NormalizedStringOptions(normalize_to_uppercase=True, normalize_to_lowercase=True)
