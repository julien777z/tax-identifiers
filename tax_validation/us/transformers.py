from typing import Final

from tax_validation.enums import TaxIdentifierOrigin, TinType
from tax_validation.normalization import collapse_whitespace
from tax_validation.us.enums import USState
from tax_validation.us.tax_identifiers import (
    ComparableUsTaxIdentifier,
    clean_us_tax_identifier,
    format_us_ein,
    strict_format_us_ssn,
)

US_STATE_BY_CODE: Final[dict[str, USState]] = {state.value: state for state in USState}
US_STATE_BY_NAME: Final[dict[str, USState]] = {
    state.name.replace("_", " "): state for state in USState
}


def transform_us_state(value: str | USState) -> USState:
    """Resolve a 2-letter postal code or full state name to a USState member."""

    if isinstance(value, USState):
        return value

    normalized = collapse_whitespace(value).upper()
    resolved = US_STATE_BY_CODE.get(normalized) or US_STATE_BY_NAME.get(normalized)

    if resolved is None:
        raise ValueError(f"Unknown US state: {value!r}")

    return resolved


def transform_tax_identifier(
    value: str | None,
    *,
    origin: TaxIdentifierOrigin,
    tin_type: TinType | None = None,
) -> str | None:
    """Normalize a tax identifier with origin-aware strictness."""

    if value is None:
        return None

    normalized_value = collapse_whitespace(value).upper()

    if not normalized_value:
        return None

    if "*" in normalized_value:
        raise ValueError("Tax ID cannot contain mask characters")

    if origin == TaxIdentifierOrigin.US_TIN or tin_type in {TinType.SSN, TinType.EIN}:
        return clean_us_tax_identifier(normalized_value)

    return normalized_value


def transform_tax_id_field(
    value: str | None,
    *,
    origin: TaxIdentifierOrigin,
    tin_type: TinType | None,
    allow_masked: bool,
) -> str | ComparableUsTaxIdentifier | None:
    """Normalize tax IDs and preserve comparable US display strings."""

    normalized_input = collapse_whitespace(value).upper()

    if not normalized_input:
        return None

    if "*" in normalized_input:
        if allow_masked:
            return normalized_input

        raise ValueError("Tax ID cannot contain mask characters")

    normalized_value = transform_tax_identifier(
        normalized_input,
        origin=origin,
        tin_type=tin_type,
    )

    if normalized_value is None:
        return None

    if origin == TaxIdentifierOrigin.US_TIN:
        return ComparableUsTaxIdentifier(normalized_input)

    return normalized_value


def transform_ssn_formatted(ssn: str | int | None) -> str | None:
    """Validate and normalize an SSN as a formatted string, raising for non-9-digit input."""

    return strict_format_us_ssn(ssn)


def transform_ein_formatted(ein: str | int | None) -> str | None:
    """Validate and normalize an EIN as a formatted string."""

    return format_us_ein(ein)
