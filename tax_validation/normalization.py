import re
from collections.abc import Callable
from typing import Final

NON_DIGIT_PATTERN: Final[re.Pattern[str]] = re.compile(r"\D+")


def strip_non_digits(value: str) -> str:
    """Remove every non-digit character from a string."""

    return NON_DIGIT_PATTERN.sub("", value)


def collapse_whitespace(value: str) -> str:
    """Collapse consecutive whitespace and trim leading and trailing whitespace."""

    if not isinstance(value, str):
        raise ValueError("Value must be a string")

    return re.sub(r"\s+", " ", value).strip()


def empty_str_to_none(data: dict[str, object]) -> dict[str, object]:
    """Return a copy of the mapping with empty or whitespace-only strings replaced by None."""

    return {
        key: None if isinstance(value, str) and value.strip() == "" else value
        for key, value in data.items()
    }


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
