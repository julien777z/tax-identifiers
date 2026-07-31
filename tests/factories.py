from polyfactory.decorators import post_generated
from polyfactory.factories.pydantic_factory import ModelFactory

from tax_identifiers import (
    Country,
    TaxIdentifier,
    TaxIdentifierType,
    mask_tax_id,
)
from tests.models import (
    LenientSsnTaxPayer,
    MaskedTaxIdAliasSet,
    UntaxedParty,
    SsnTaxPayer,
    TaxIdAliasSet,
)

FOREIGN_TAX_ID_PREFIX = "GB"


def generate_tax_id(
    tax_id_type: TaxIdentifierType = TaxIdentifierType.SSN,
    *,
    area: str | None = None,
    group: str | None = None,
    serial: str | None = None,
) -> str:
    """Generate a structurally valid tax identifier for the requested type."""

    if tax_id_type == TaxIdentifierType.FOREIGN_TIN:
        return f"{FOREIGN_TAX_ID_PREFIX}{ModelFactory.__random__.randint(0, 99_999_999):08d}"

    resolved_area = (
        area or f"{ModelFactory.__random__.choice([*range(1, 666), *range(667, 900)]):03d}"
    )
    resolved_group = group or f"{ModelFactory.__random__.randint(1, 99):02d}"
    resolved_serial = serial or f"{ModelFactory.__random__.randint(1, 9999):04d}"

    return f"{resolved_area}{resolved_group}{resolved_serial}"


def generate_full_name() -> str:
    """Generate a person's full name."""

    return ModelFactory.__faker__.name()


def generate_masked_tax_id(*, plain: bool = False) -> str:
    """Generate a masked tax identifier, optionally as a plain string from a serialized payload."""

    masked = mask_tax_id(generate_tax_id(TaxIdentifierType.SSN))

    return str(masked) if plain else masked


class TaxIdentifierFactory(ModelFactory[TaxIdentifier]):
    """Factory for TaxIdentifier."""

    __model__ = TaxIdentifier

    @classmethod
    def country(cls) -> Country:
        """Default to the United States."""

        return Country.US

    @classmethod
    def tax_id_type(cls) -> TaxIdentifierType:
        """Default to an SSN."""

        return TaxIdentifierType.SSN

    @post_generated
    @classmethod
    def tax_id(cls, tax_id_type: TaxIdentifierType) -> str:
        """Generate an identifier matching the resolved type."""

        return generate_tax_id(tax_id_type)


class SsnTaxPayerFactory(ModelFactory[SsnTaxPayer]):
    """Factory for SsnTaxPayer."""

    __model__ = SsnTaxPayer

    @classmethod
    def tax_id(cls) -> str:
        """Generate an SSN the strict field accepts."""

        return generate_tax_id(TaxIdentifierType.SSN)


class LenientSsnTaxPayerFactory(ModelFactory[LenientSsnTaxPayer]):
    """Factory for LenientSsnTaxPayer."""

    __model__ = LenientSsnTaxPayer

    @classmethod
    def tax_id(cls) -> str:
        """Generate an SSN the lenient field accepts."""

        return generate_tax_id(TaxIdentifierType.SSN)


class UntaxedPartyFactory(ModelFactory[UntaxedParty]):
    """Factory for UntaxedParty."""

    __model__ = UntaxedParty

    @classmethod
    def name(cls) -> str:
        """Generate a business name."""

        return cls.__faker__.company()


class TaxIdAliasSetFactory(ModelFactory[TaxIdAliasSet]):
    """Factory for TaxIdAliasSet."""

    __model__ = TaxIdAliasSet

    @classmethod
    def ssn(cls) -> str:
        """Generate an SSN."""

        return generate_tax_id(TaxIdentifierType.SSN)

    @classmethod
    def lenient_ssn(cls) -> str:
        """Generate an SSN."""

        return generate_tax_id(TaxIdentifierType.SSN)

    @classmethod
    def us(cls) -> str:
        """Generate a US identifier of unspecified type."""

        return generate_tax_id(TaxIdentifierType.SSN)

    @classmethod
    def foreign(cls) -> str:
        """Generate a foreign TIN."""

        return generate_tax_id(TaxIdentifierType.FOREIGN_TIN)

    @classmethod
    def unknown(cls) -> str:
        """Generate a country-agnostic identifier."""

        return generate_tax_id(TaxIdentifierType.SSN)


class MaskedTaxIdAliasSetFactory(ModelFactory[MaskedTaxIdAliasSet]):
    """Factory for MaskedTaxIdAliasSet."""

    __model__ = MaskedTaxIdAliasSet

    @classmethod
    def us(cls) -> str:
        """Generate a masked US identifier."""

        return generate_masked_tax_id()

    @classmethod
    def foreign(cls) -> str:
        """Generate a masked foreign TIN."""

        return generate_masked_tax_id()

    @classmethod
    def unknown(cls) -> str:
        """Generate a masked country-agnostic identifier."""

        return generate_masked_tax_id()
