from typing import Annotated, Final, TypeAlias

from pydantic import BeforeValidator

from tax_identifiers.annotations import TaxIdFieldOptions
from tax_identifiers.countries import Country
from tax_identifiers.enums import TaxIdentifierType
from tax_identifiers.normalization import transform_required_string

StrRequired: TypeAlias = Annotated[str, "str_required", BeforeValidator(transform_required_string)]

TaxIdStr: TypeAlias = Annotated[str, "tax_id"]

SSN_OPTIONS: Final[TaxIdFieldOptions] = TaxIdFieldOptions(
    country=Country.US, tax_id_type=TaxIdentifierType.SSN
)
US_OPTIONS: Final[TaxIdFieldOptions] = TaxIdFieldOptions(country=Country.US)
FOREIGN_OPTIONS: Final[TaxIdFieldOptions] = TaxIdFieldOptions(
    tax_id_type=TaxIdentifierType.FOREIGN_TIN
)
UNKNOWN_OPTIONS: Final[TaxIdFieldOptions] = TaxIdFieldOptions()

LENIENT_SSN_OPTIONS: Final[TaxIdFieldOptions] = TaxIdFieldOptions(
    country=Country.US, tax_id_type=TaxIdentifierType.SSN, assert_validity=False
)

MASKABLE_US_OPTIONS: Final[TaxIdFieldOptions] = TaxIdFieldOptions(
    country=Country.US, allow_masked=True
)
MASKABLE_FOREIGN_OPTIONS: Final[TaxIdFieldOptions] = TaxIdFieldOptions(
    tax_id_type=TaxIdentifierType.FOREIGN_TIN, allow_masked=True
)
MASKABLE_UNKNOWN_OPTIONS: Final[TaxIdFieldOptions] = TaxIdFieldOptions(allow_masked=True)

SSNTaxIdField: TypeAlias = Annotated[TaxIdStr, SSN_OPTIONS]

LenientSSNTaxIdField: TypeAlias = Annotated[TaxIdStr, LENIENT_SSN_OPTIONS]

USTaxIdField: TypeAlias = Annotated[TaxIdStr, US_OPTIONS]

ForeignTaxIdField: TypeAlias = Annotated[TaxIdStr, FOREIGN_OPTIONS]

UnknownTaxIdField: TypeAlias = Annotated[TaxIdStr, UNKNOWN_OPTIONS]

MaskableUSTaxIdField: TypeAlias = Annotated[TaxIdStr, MASKABLE_US_OPTIONS]

MaskableForeignTaxIdField: TypeAlias = Annotated[TaxIdStr, MASKABLE_FOREIGN_OPTIONS]

MaskableUnknownTaxIdField: TypeAlias = Annotated[TaxIdStr, MASKABLE_UNKNOWN_OPTIONS]
