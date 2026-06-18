from collections.abc import Callable
from typing import Annotated

from pydantic import AfterValidator, BeforeValidator

from tax_validation.normalization import build_string_normalizer, transform_required_string


def NormalizedString(  # pylint: disable=invalid-name
    label: str = "normalized_string",
    *,
    normalize_to_uppercase: bool = False,
    normalize_to_lowercase: bool = False,
    normalize_to_titlecase: bool = False,
    strip_non_digits: bool = False,
    strip_trailing_punctuation: bool = False,
) -> object:
    """Return an annotated string type with configurable normalization steps."""

    normalizer = build_string_normalizer(
        normalize_to_uppercase=normalize_to_uppercase,
        normalize_to_lowercase=normalize_to_lowercase,
        normalize_to_titlecase=normalize_to_titlecase,
        strip_non_digits=strip_non_digits,
        strip_trailing_punctuation=strip_trailing_punctuation,
    )

    return Annotated[str, label, AfterValidator(normalizer)]


def StringBool(  # pylint: disable=invalid-name
    *,
    predicate: Callable[[str], bool],
    label: str = "string_bool",
) -> object:
    """Return an annotated bool field that converts strings via a caller-supplied predicate."""

    def _transform(value: bool | str) -> bool:
        if isinstance(value, bool):
            return value

        return predicate(str(value))

    return Annotated[bool, label, BeforeValidator(_transform)]


StrRequired = Annotated[str, "str_required", BeforeValidator(transform_required_string)]
