from typing import Annotated, TypeAlias

from pydantic import BeforeValidator

from tax_identifiers.annotations import TaxIdFieldOptions
from tax_identifiers.countries import Country
from tax_identifiers.enums import TaxIdentifierType
from tax_identifiers.normalization import transform_required_string

StrRequired: TypeAlias = Annotated[str, "str_required", BeforeValidator(transform_required_string)]

TaxIdStr: TypeAlias = Annotated[str, "tax_id"]

SSNTaxIdField: TypeAlias = Annotated[
    TaxIdStr, TaxIdFieldOptions(country=Country.US, tax_id_type=TaxIdentifierType.SSN)
]

LenientSSNTaxIdField: TypeAlias = Annotated[
    TaxIdStr,
    TaxIdFieldOptions(country=Country.US, tax_id_type=TaxIdentifierType.SSN, assert_validity=False),
]

USTaxIdField: TypeAlias = Annotated[
    TaxIdStr,
    TaxIdFieldOptions(country=Country.US, tax_id_type=TaxIdentifierType.US_UNSPECIFIED),
]

ForeignTaxIdField: TypeAlias = Annotated[
    TaxIdStr, TaxIdFieldOptions(tax_id_type=TaxIdentifierType.FOREIGN_TIN)
]

UnknownTaxIdField: TypeAlias = Annotated[TaxIdStr, TaxIdFieldOptions()]
