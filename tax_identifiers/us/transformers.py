from typing import Final

from tax_identifiers.enums import TaxIdentifierOrigin, TinType
from tax_identifiers.normalization import collapse_whitespace
from tax_identifiers.us.enums import USState
from tax_identifiers.us.tax_identifiers import clean_us_tax_identifier

US_STATE_BY_CODE: Final[dict[str, USState]] = {state.value: state for state in USState}
US_STATE_BY_NAME: Final[dict[str, USState]] = {
    state.name.replace("_", " "): state for state in USState
}


def requires_us_cleaning(origin: TaxIdentifierOrigin, tin_type: TinType | None) -> bool:
    """Return whether an origin and tin type must normalize to nine US digits."""

    return origin == TaxIdentifierOrigin.US_TIN or tin_type in {TinType.SSN, TinType.EIN}


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

    if requires_us_cleaning(origin, tin_type):
        return clean_us_tax_identifier(normalized_value)

    return normalized_value
