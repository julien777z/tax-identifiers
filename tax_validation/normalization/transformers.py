import re
from collections.abc import Callable
from typing import Final

from tax_validation.enums import TaxIdentifierOrigin, TinType, USState
from tax_validation.normalization.tax_identifiers import (
    NON_DIGIT_PATTERN,
    ComparableUsTaxIdentifier,
    clean_us_tax_identifier,
    format_us_ein,
    strict_format_us_ssn,
)

US_STATE_BY_CODE: Final[dict[str, USState]] = {state.value: state for state in USState}
US_STATE_BY_NAME: Final[dict[str, USState]] = {
    state.name.replace("_", " "): state for state in USState
}


def collapse_whitespace(value: str) -> str:
    """Collapse consecutive whitespace and trim leading and trailing whitespace."""

    if not isinstance(value, str):
        raise ValueError("Value must be a string")

    return re.sub(r"\s+", " ", value).strip()


def empty_str_to_none(data: dict[str, object]) -> dict[str, object]:
    """Convert empty or whitespace-only strings to None for all string fields."""

    for key, value in list(data.items()):
        if isinstance(value, str) and value.strip() == "":
            data[key] = None

    return data


def transform_required_string(value: str | None) -> str:
    """Normalize a required string and reject empty values."""

    if value is None:
        raise ValueError("Value cannot be empty")

    normalized_value = collapse_whitespace(value)

    if not normalized_value:
        raise ValueError("Value cannot be empty")

    return normalized_value


def build_string_normalizer(
    *,
    normalize_to_uppercase: bool = False,
    normalize_to_lowercase: bool = False,
    normalize_to_titlecase: bool = False,
    strip_non_digits: bool = False,
    strip_trailing_punctuation: bool = False,
) -> Callable[[str], str]:
    """Build a composable string normalizer from normalization options."""

    def _normalize(value: str) -> str:
        result = collapse_whitespace(value)

        if normalize_to_uppercase:
            result = result.upper()
        elif normalize_to_lowercase:
            result = result.lower()
        elif normalize_to_titlecase:
            result = result.title()

        if strip_trailing_punctuation:
            result = " ".join(token for token in (t.rstrip(".,") for t in result.split()) if token)

        if strip_non_digits:
            result = NON_DIGIT_PATTERN.sub("", result)

        return result

    return _normalize


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
