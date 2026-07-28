from collections.abc import Callable

import pytest
from pydantic import ValidationError

from tax_identifiers import (
    ComparableUsTaxIdentifier,
    Country,
    TaxIdFieldOptions,
    TaxIdentifierType,
    format_us_ssn,
    is_masked_tax_id,
)
from tax_identifiers.us.enums import USState
from tests.conftest import (
    InlineUsTaxIdHolder,
    MaskedTaxIdHolder,
    StateHolder,
    UnknownTaxIdHolder,
    UsTaxIdHolder,
)


class TestUSStateField:
    """Test that US states coerce from codes and names."""

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
    """Test that the tax identifier field annotation normalizes and rejects input."""

    def test_normalizes_us_identifier(self, tax_id_factory: Callable[..., str]) -> None:
        """Test that a US identifier is stored as a formatting-insensitive value."""

        raw_tax_id = tax_id_factory(TaxIdentifierType.SSN)
        holder = UsTaxIdHolder(tax_id=format_us_ssn(raw_tax_id))

        assert isinstance(holder.tax_id, ComparableUsTaxIdentifier)
        assert holder.tax_id == raw_tax_id

    def test_rejects_masked_value_by_default(
        self, masked_tax_id_factory: Callable[..., str]
    ) -> None:
        """Test that a masked tax identifier is rejected unless masking is allowed."""

        with pytest.raises(ValidationError, match="Tax ID cannot contain mask characters"):
            UsTaxIdHolder(tax_id=masked_tax_id_factory())

    def test_rejects_non_string_value(self, tax_id_factory: Callable[..., str]) -> None:
        """Test that a non-string tax identifier is rejected without a type error."""

        with pytest.raises(ValidationError):
            UsTaxIdHolder(tax_id=int(tax_id_factory(TaxIdentifierType.SSN)))

    @pytest.mark.parametrize("plain", [False, True], ids=["maskable_type", "plain_string"])
    def test_accepts_masked_value_when_configured(
        self, masked_tax_id_factory: Callable[..., str], plain: bool
    ) -> None:
        """Test that a masked tax identifier passes through when masking is allowed."""

        masked = masked_tax_id_factory(plain=plain)
        holder = MaskedTaxIdHolder(tax_id=masked)

        assert holder.tax_id == masked
        assert is_masked_tax_id(holder.tax_id)


class TestUnknownCountryTaxIdField:
    """Test that the country-agnostic field normalizes without country rules."""

    def test_normalizes_generically(self, normalizable_foreign_tax_id: tuple[str, str]) -> None:
        """Test that an unknown-country field uppercases without US cleaning."""

        raw, normalized = normalizable_foreign_tax_id
        holder = UnknownTaxIdHolder(tax_id=raw)

        assert holder.tax_id == normalized


class TestInlineTaxIdFieldOptions:
    """Test that a tax identifier field configured inline matches a shipped alias."""

    def test_matches_the_equivalent_alias(self, tax_id_factory: Callable[..., str]) -> None:
        """Test that an inline annotation behaves identically to the matching alias."""

        formatted = format_us_ssn(tax_id_factory(TaxIdentifierType.SSN))

        inline = InlineUsTaxIdHolder(tax_id=formatted)
        aliased = UsTaxIdHolder(tax_id=formatted)

        assert inline.tax_id == aliased.tax_id
        assert type(inline.tax_id) is type(aliased.tax_id)


class TestTaxIdFieldOptions:
    """Test that annotation metadata defaults to the country-agnostic contract."""

    def test_defaults_to_the_country_agnostic_contract(self) -> None:
        """Test that options default to the unknown country without allowing masked input."""

        options = TaxIdFieldOptions()

        assert options.country is Country.UNKNOWN
        assert not options.allow_masked
