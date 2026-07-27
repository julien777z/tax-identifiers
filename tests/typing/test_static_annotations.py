"""Every shipped field type used in real annotation position.

This module is the static-typing regression guard: a type checker must accept every
annotation below. Field types used to be factory functions called in annotation position
(``tax_id: TaxIdField(country=Country.US)``), which no type checker can accept because a
call is not a valid type expression. Adding one back would fail pyright here.
"""

from typing import Annotated

from tax_identifiers import (
    BaseModel,
    Country,
    DigitsOnlyString,
    EINFormattedField,
    EINTaxIdField,
    ForeignTaxIdField,
    ITINTaxIdField,
    LowercaseString,
    MaskableEINTaxIdField,
    MaskableForeignTaxIdField,
    MaskableITINTaxIdField,
    MaskableSSNTaxIdField,
    MaskableUnknownTaxIdField,
    MaskableUSTaxIdField,
    NormalizedStringOptions,
    SSNFormattedField,
    SSNTaxIdField,
    StringBoolOptions,
    StrRequired,
    TaxIdentifierType,
    TaxIdentifierTypeField,
    TaxIdFieldOptions,
    TitlecaseString,
    UnknownTaxIdField,
    UppercaseString,
    USStateField,
    USTaxIdField,
)


def is_affirmative(value: str) -> bool:
    """Return whether a string token is an affirmative answer."""

    return value.strip().upper() in {"YES", "Y", "TRUE"}


FrenchTinField = Annotated[
    str,
    "tax_id",
    TaxIdFieldOptions(country=Country.FR, tax_id_type=TaxIdentifierType.FOREIGN_TIN),
]

BusinessName = Annotated[str, "normalized_string", NormalizedStringOptions(strip_trailing_punctuation=True)]

Consent = Annotated[bool, "string_bool", StringBoolOptions(predicate=is_affirmative)]


class TaxIdFieldHolder(BaseModel):
    """Model annotated with every shipped tax identifier alias."""

    ssn: SSNTaxIdField
    ein: EINTaxIdField
    itin: ITINTaxIdField
    us: USTaxIdField
    foreign: ForeignTaxIdField
    unknown: UnknownTaxIdField


class MaskableTaxIdFieldHolder(BaseModel):
    """Model annotated with every shipped mask-accepting tax identifier alias."""

    ssn: MaskableSSNTaxIdField
    ein: MaskableEINTaxIdField
    itin: MaskableITINTaxIdField
    us: MaskableUSTaxIdField
    foreign: MaskableForeignTaxIdField
    unknown: MaskableUnknownTaxIdField


class StringFieldHolder(BaseModel):
    """Model annotated with every shipped string alias."""

    required: StrRequired
    upper: UppercaseString
    lower: LowercaseString
    title: TitlecaseString
    digits: DigitsOnlyString


class FormattedFieldHolder(BaseModel):
    """Model annotated with the formatting-only aliases."""

    ein: EINFormattedField
    ssn: SSNFormattedField
    state: USStateField
    tax_id_type: TaxIdentifierTypeField


class CustomAnnotationHolder(BaseModel):
    """Model annotated with caller-built annotations rather than shipped aliases."""

    tax_id: FrenchTinField
    business_name: BusinessName
    consented: Consent


class InlineAnnotationHolder(BaseModel):
    """Model configuring options inline in annotation position."""

    tax_id: Annotated[str, "tax_id", TaxIdFieldOptions(country=Country.US, allow_masked=True)]
    label: Annotated[str, "normalized_string", NormalizedStringOptions(normalize_to_uppercase=True)]


def test_annotations_resolve_at_runtime() -> None:
    """Test that every annotated model above builds and validates."""

    holder = TaxIdFieldHolder(
        ssn="123-45-6789",
        ein="12-3456789",
        itin="912-45-6789",
        us="123456789",
        foreign="gb-1234",
        unknown="ab-12",
    )

    assert holder.ssn == "123456789"
    assert holder.foreign == "GB-1234"

    masked = MaskableTaxIdFieldHolder(
        ssn="*****6789",
        ein="*****6789",
        itin="*****6789",
        us="*****6789",
        foreign="*****6789",
        unknown="*****6789",
    )

    assert masked.ssn == "*****6789"

    strings = StringFieldHolder(
        required="  spaced  out  ",
        upper="acme llc",
        lower="ACME LLC",
        title="acme llc",
        digits="12-34",
    )

    assert (strings.required, strings.upper, strings.lower) == ("spaced out", "ACME LLC", "acme llc")
    assert (strings.title, strings.digits) == ("Acme Llc", "1234")

    # String input for a bool field is wider than the field's own type, so it goes through
    # model_validate rather than the constructor.
    custom = CustomAnnotationHolder.model_validate(
        {"tax_id": "fr-123.", "business_name": "acme llc.", "consented": "yes"}
    )

    assert (custom.tax_id, custom.business_name, custom.consented) == ("FR-123.", "acme llc", True)
