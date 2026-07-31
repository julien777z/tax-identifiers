from collections.abc import Callable
from typing import Annotated, Final

import pytest
from pydantic import TypeAdapter, ValidationError

from tax_identifiers import (
    ComparableUsTaxIdentifier,
    Country,
    SSNTaxIdField,
    TaxIdFieldOptions,
    TaxIdStr,
    TaxIdentifierType,
    UnsupportedTaxIdTypeError,
    USTaxIdField,
    format_us_ssn,
    is_masked_tax_id,
)
from tax_identifiers.base import BaseModel
from tax_identifiers.us.enums import USState
from tests.conftest import (
    LenientTaxIdentifierHolder,
    MaskableTaxIdFieldHolder,
    StateHolder,
    TaxIdentifierHolder,
    TaxIdFieldHolder,
)

RESERVED_SSN_SEGMENTS: Final[list[dict[str, str]]] = [
    {"area": "000"},
    {"area": "666"},
    {"area": "900"},
    {"group": "00"},
    {"serial": "0000"},
]
RESERVED_SSN_SEGMENT_IDS: Final[list[str]] = [
    "zero_area",
    "reserved_area",
    "high_area",
    "zero_group",
    "zero_serial",
]


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

    def test_normalizes_us_identifier(
        self,
        tax_id_factory: Callable[..., str],
        tax_id_field_holder_factory: Callable[..., TaxIdFieldHolder],
    ) -> None:
        """Test that a US identifier is stored as a formatting-insensitive value."""

        raw_tax_id = tax_id_factory(TaxIdentifierType.SSN)
        holder = tax_id_field_holder_factory(us=format_us_ssn(raw_tax_id))

        assert isinstance(holder.us, ComparableUsTaxIdentifier)
        assert holder.us == raw_tax_id

    def test_rejects_masked_value_by_default(
        self,
        masked_tax_id_factory: Callable[..., str],
        tax_id_field_holder_factory: Callable[..., TaxIdFieldHolder],
    ) -> None:
        """Test that a masked tax identifier is rejected unless masking is allowed."""

        with pytest.raises(ValidationError, match="Tax ID cannot contain mask characters"):
            tax_id_field_holder_factory(us=masked_tax_id_factory())

    def test_rejects_non_string_value(
        self,
        tax_id_factory: Callable[..., str],
        tax_id_field_holder_factory: Callable[..., TaxIdFieldHolder],
    ) -> None:
        """Test that a non-string tax identifier is rejected without a type error."""

        with pytest.raises(ValidationError):
            tax_id_field_holder_factory(us=int(tax_id_factory(TaxIdentifierType.SSN)))

    @pytest.mark.parametrize(
        "field_name",
        ["ssn", "us", "foreign", "unknown"],
        ids=["ssn", "us_unspecified", "foreign", "unknown"],
    )
    def test_every_alias_rejects_masked_input_without_the_marker(
        self,
        field_name: str,
        masked_tax_id_factory: Callable[..., str],
        tax_id_field_holder_factory: Callable[..., TaxIdFieldHolder],
    ) -> None:
        """Test that rejecting a masked value is the default every alias keeps on its own."""

        with pytest.raises(ValidationError, match="Tax ID cannot contain mask characters"):
            tax_id_field_holder_factory(**{field_name: masked_tax_id_factory()})

    @pytest.mark.parametrize("plain", [False, True], ids=["maskable_type", "plain_string"])
    def test_accepts_masked_value_when_configured(
        self,
        masked_tax_id_factory: Callable[..., str],
        maskable_tax_id_field_holder_factory: Callable[..., MaskableTaxIdFieldHolder],
        plain: bool,
    ) -> None:
        """Test that a masked tax identifier passes through when masking is allowed."""

        masked = masked_tax_id_factory(plain=plain)
        holder = maskable_tax_id_field_holder_factory(us=masked)

        assert holder.us == masked
        assert is_masked_tax_id(holder.us)


class TestUnknownCountryTaxIdField:
    """Test that the country-agnostic field normalizes without country rules."""

    def test_normalizes_generically(
        self,
        normalizable_foreign_tax_id: tuple[str, str],
        tax_id_field_holder_factory: Callable[..., TaxIdFieldHolder],
    ) -> None:
        """Test that an unknown-country field uppercases without US cleaning."""

        raw, normalized = normalizable_foreign_tax_id

        assert tax_id_field_holder_factory(unknown=raw).unknown == normalized


class TestInlineTaxIdFieldOptions:
    """Test that a tax identifier field configured inline matches a shipped alias."""

    def test_matches_the_equivalent_alias(self, tax_id_factory: Callable[..., str]) -> None:
        """Test that an inline annotation behaves identically to the matching alias."""

        formatted = format_us_ssn(tax_id_factory(TaxIdentifierType.SSN))
        inline_adapter: TypeAdapter[str] = TypeAdapter(
            Annotated[
                TaxIdStr,
                TaxIdFieldOptions(country=Country.US, tax_id_type=TaxIdentifierType.US_UNSPECIFIED),
            ]
        )
        aliased_adapter: TypeAdapter[str] = TypeAdapter(USTaxIdField)

        inline = inline_adapter.validate_python(formatted)
        aliased = aliased_adapter.validate_python(formatted)

        assert inline == aliased
        assert type(inline) is type(aliased)


class TestMixinNormalizationEquivalence:
    """Test that the masking mixin does not change how a tax identifier field normalizes."""

    def test_stored_value_matches_the_bare_annotation(
        self, tax_id_factory: Callable[..., str]
    ) -> None:
        """Test that a mixin-bearing SSN field stores exactly what its annotation produces."""

        formatted = format_us_ssn(tax_id_factory(TaxIdentifierType.SSN))
        annotation_adapter: TypeAdapter[str] = TypeAdapter(SSNTaxIdField)

        mixin_value = TaxIdentifierHolder(tax_id=formatted).tax_id
        annotation_value = annotation_adapter.validate_python(formatted)

        assert mixin_value == annotation_value
        assert type(mixin_value) is type(annotation_value)


class TestTaxIdFieldOptions:
    """Test that annotation metadata defaults to the country-agnostic contract."""

    def test_defaults_to_the_country_agnostic_contract(self) -> None:
        """Test that options default to the unknown country and its country-agnostic type."""

        options = TaxIdFieldOptions()

        assert options.country is Country.UNKNOWN
        assert options.tax_id_type is TaxIdentifierType.NONE
        assert options.assert_validity


class TestUnsupportedTaxIdTypeDeclaration:
    """Test that a field declared with a type its country does not handle is rejected."""

    @pytest.mark.parametrize(
        ("country", "tax_id_type"),
        [
            (Country.US, TaxIdentifierType.NONE),
            (Country.US, TaxIdentifierType.FOREIGN_TIN),
            (Country.UNKNOWN, TaxIdentifierType.SSN),
            (Country.FR, TaxIdentifierType.US_UNSPECIFIED),
        ],
        ids=["us_none", "us_foreign", "unknown_ssn", "named_us_unspecified"],
    )
    def test_rejects_a_pair_the_country_does_not_handle(
        self, country: Country, tax_id_type: TaxIdentifierType
    ) -> None:
        """Test that declaring an unsupported country and type pair fails when the schema is built."""

        with pytest.raises(UnsupportedTaxIdTypeError):
            TypeAdapter(
                Annotated[TaxIdStr, TaxIdFieldOptions(country=country, tax_id_type=tax_id_type)]
            )


class TestSsnStructuralValidation:
    """Test that the SSN field rejects identifiers its country's rules find invalid."""

    @pytest.mark.parametrize(
        ("holder", "rejects"),
        [(TaxIdentifierHolder, True), (LenientTaxIdentifierHolder, False)],
        ids=["strict", "lenient"],
    )
    @pytest.mark.parametrize("segments", RESERVED_SSN_SEGMENTS, ids=RESERVED_SSN_SEGMENT_IDS)
    def test_reserved_identifiers_are_rejected_only_when_validity_is_asserted(
        self,
        tax_id_factory: Callable[..., str],
        segments: dict[str, str],
        holder: type[TaxIdentifierHolder] | type[LenientTaxIdentifierHolder],
        rejects: bool,
    ) -> None:
        """Test that each reserved SSN segment is rejected by the strict field and kept by the lenient one."""

        reserved = tax_id_factory(TaxIdentifierType.SSN, **segments)

        if rejects:
            with pytest.raises(ValidationError, match="is not a valid"):
                holder(tax_id=reserved)
        else:
            assert holder(tax_id=reserved).tax_id == reserved

    @pytest.mark.parametrize(
        "holder",
        [TaxIdentifierHolder, LenientTaxIdentifierHolder],
        ids=["strict", "lenient"],
    )
    def test_normalizes_a_structurally_valid_identifier(
        self,
        tax_id_factory: Callable[..., str],
        holder: type[TaxIdentifierHolder] | type[LenientTaxIdentifierHolder],
    ) -> None:
        """Test that both fields normalize a valid SSN the same way."""

        raw_tax_id = tax_id_factory(TaxIdentifierType.SSN)

        assert holder(tax_id=format_us_ssn(raw_tax_id)).tax_id == raw_tax_id

    def test_lenient_field_still_declares_the_ssn_type(
        self, tax_id_factory: Callable[..., str]
    ) -> None:
        """Test that the lenient field keeps the country and type metadata it was declared with."""

        holder = LenientTaxIdentifierHolder(
            tax_id=tax_id_factory(TaxIdentifierType.SSN, area="666")
        )
        options = holder.tax_id_field_options("tax_id")

        assert options is not None
        assert options.country is Country.US
        assert options.tax_id_type is TaxIdentifierType.SSN


class TestPermissiveTaxIdFields:
    """Test that fields whose rules cannot assert validity keep accepting their input."""

    @pytest.mark.parametrize(
        "field_name",
        ["us", "foreign", "unknown"],
        ids=["us_unspecified", "foreign", "unknown"],
    )
    def test_accepts_values_the_ssn_field_rejects(
        self,
        field_name: str,
        tax_id_factory: Callable[..., str],
        tax_id_field_holder_factory: Callable[..., TaxIdFieldHolder],
    ) -> None:
        """Test that a value reserved for SSNs still passes fields without SSN rules."""

        reserved = tax_id_factory(TaxIdentifierType.SSN, area="666")
        holder = tax_id_field_holder_factory(**{field_name: reserved})

        assert getattr(holder, field_name) == reserved

    def test_named_country_without_rules_is_accepted(self) -> None:
        """Test that a country with no dedicated rules does not fail validation."""

        class FrenchTinHolder(BaseModel):
            """Test model with a French foreign-TIN field."""

            tax_id: Annotated[
                TaxIdStr,
                TaxIdFieldOptions(country=Country.FR, tax_id_type=TaxIdentifierType.FOREIGN_TIN),
            ]

        assert FrenchTinHolder(tax_id=" fr-123 ").tax_id == "FR-123"
