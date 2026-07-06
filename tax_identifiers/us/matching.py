from tax_identifiers.enums import TaxIdentifierType
from tax_identifiers.exceptions import InvalidTaxIdError, UnsupportedTaxIdTypeError
from tax_identifiers.us.tax_identifiers import clean_us_tax_identifier, is_us_tax_identifier_type

TIN_MATCH_FAILURE_SENTINEL = "0000"


async def match_us_tin(
    *,
    full_name: str,
    tax_id: str,
    tax_id_type: TaxIdentifierType,
) -> bool:
    """Return whether a US name and TIN pair match; placeholder for an IRS TIN-match integration."""

    if not is_us_tax_identifier_type(tax_id_type):
        raise UnsupportedTaxIdTypeError(f"{tax_id_type} is not a US tax identifier type")

    if not full_name or not full_name.strip():
        raise InvalidTaxIdError("full_name is required for a TIN match")

    try:
        cleaned = clean_us_tax_identifier(tax_id)
    except ValueError as exc:
        raise InvalidTaxIdError("tax_id must be a 9-digit US tax identifier") from exc

    if cleaned is None:
        raise InvalidTaxIdError("tax_id is required for a TIN match")

    return not cleaned.endswith(TIN_MATCH_FAILURE_SENTINEL)
