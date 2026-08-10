import re
from typing import Final

NON_DIGIT_PATTERN: Final[re.Pattern[str]] = re.compile(r"\D+")
WHITESPACE_PATTERN: Final[re.Pattern[str]] = re.compile(r"\s+")


def strip_non_digits(value: str) -> str:
    """Remove every non-digit character from a string."""

    return NON_DIGIT_PATTERN.sub("", value)


def collapse_whitespace(value: str) -> str:
    """Collapse consecutive whitespace and trim leading and trailing whitespace."""

    return WHITESPACE_PATTERN.sub(" ", value).strip()


def empty_str_to_none(data: dict[str, object]) -> dict[str, object]:
    """Return a copy of the mapping with empty or whitespace-only strings replaced by None."""

    return {
        key: None if isinstance(value, str) and value.strip() == "" else value for key, value in data.items()
    }


def transform_required_string(value: str | None) -> str:
    """Normalize a required string and reject empty values."""

    if value is None:
        raise ValueError("Value cannot be empty")

    normalized_value = collapse_whitespace(value)

    if not normalized_value:
        raise ValueError("Value cannot be empty")

    return normalized_value
