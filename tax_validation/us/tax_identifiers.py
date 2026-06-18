from typing import Final, Self

from tax_validation.enums import TaxIdentifierType
from tax_validation.normalization import strip_non_digits

US_TAX_IDENTIFIER_TYPES: Final[frozenset[TaxIdentifierType]] = frozenset(
    {
        TaxIdentifierType.SSN,
        TaxIdentifierType.EIN,
        TaxIdentifierType.ITIN,
        TaxIdentifierType.US_UNSPECIFIED,
    }
)


def is_us_tax_identifier_type(tax_identifier_type: TaxIdentifierType | None) -> bool:
    """Return whether a tax identifier type is a US tax identifier."""

    return tax_identifier_type in US_TAX_IDENTIFIER_TYPES


def clean_us_tax_identifier(tax_identifier: str | int | None) -> str | None:
    """Normalize a US tax identifier to a 9-digit string."""

    if not tax_identifier:
        return None

    tax_identifier_digits = strip_non_digits(str(tax_identifier))

    if len(tax_identifier_digits) != 9:
        raise ValueError("Tax ID must be 9 digits")

    return tax_identifier_digits


def format_us_ssn(tax_identifier: str | int | None) -> str | None:
    """Normalize a US SSN with dashes (XXX-XX-XXXX), inserting dashes as digits are entered."""

    if tax_identifier is None:
        return None

    value = str(tax_identifier).strip()

    if not value:
        return None

    digits = strip_non_digits(value)[:9]

    if not digits:
        return None

    if len(digits) <= 3:
        return digits

    if len(digits) <= 5:
        return f"{digits[:3]}-{digits[3:]}"

    return f"{digits[:3]}-{digits[3:5]}-{digits[5:]}"


def strict_format_us_ssn(ssn: str | int | None) -> str | None:
    """Format a US SSN as XXX-XX-XXXX, raising when input is not exactly 9 digits."""

    cleaned = clean_us_tax_identifier(ssn)

    if cleaned is None:
        return None

    return f"{cleaned[:3]}-{cleaned[3:5]}-{cleaned[5:]}"


def format_us_ein(tax_identifier: str | int | None) -> str | None:
    """Validate and normalize a US EIN as a formatted string (XX-XXXXXXX)."""

    cleaned_tax_identifier = clean_us_tax_identifier(tax_identifier)

    if not cleaned_tax_identifier:
        return None

    return f"{cleaned_tax_identifier[:2]}-{cleaned_tax_identifier[2:]}"


class ComparableUsTaxIdentifier(str):
    """Comparable US tax ID string that ignores formatting in equality."""

    _normalized_tax_identifier: str | None

    def __new__(cls, value: str | int) -> Self:
        """Create a comparable US tax identifier wrapper."""

        normalized_tax_identifier = clean_us_tax_identifier(value)
        result = super().__new__(cls, value)
        result._normalized_tax_identifier = normalized_tax_identifier

        return result

    def __eq__(self, other: object) -> bool:
        """Compare by normalized digits, accepting dashed or plain strings."""

        if self._normalized_tax_identifier is None:
            return other is None

        if isinstance(other, ComparableUsTaxIdentifier):
            return (
                other._normalized_tax_identifier is not None
                and str.__eq__(self._normalized_tax_identifier, other._normalized_tax_identifier)
            )

        if isinstance(other, (str, int)):
            try:
                other_normalized = clean_us_tax_identifier(other)
            except ValueError:
                return False

            return (
                other_normalized is not None
                and str.__eq__(self._normalized_tax_identifier, other_normalized)
            )

        return False

    def __hash__(self) -> int:
        """Hash by normalized digits to stay compatible with equality."""

        normalized = self._normalized_tax_identifier

        return hash(normalized if normalized is not None else str(self))


def to_comparable_us_tax_identifier(value: str | None) -> ComparableUsTaxIdentifier | None:
    """Wrap a US tax identifier for normalized comparison."""

    if value is None:
        return None

    return ComparableUsTaxIdentifier(value)
