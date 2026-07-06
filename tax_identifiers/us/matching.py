from tax_identifiers.enums import TaxIdentifierType


async def match_us_tin(
    *,
    full_name: str,
    tax_id: str,
    tax_id_type: TaxIdentifierType,
) -> bool:
    """Return whether a US name and TIN pair match against the IRS TIN-matching service."""

    raise NotImplementedError("US TIN matching is not implemented yet")
