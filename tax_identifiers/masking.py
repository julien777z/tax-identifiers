from typing import Self


class MaskableTaxId(str):
    """A tax identifier string that records whether it is masked."""

    is_masked: bool

    def __new__(cls, value: str, *, is_masked: bool = False) -> Self:
        """Create a tax identifier string carrying its masked state."""

        result = super().__new__(cls, value)
        result.is_masked = is_masked

        return result


def mask_tax_id(value: str) -> MaskableTaxId:
    """Mask a tax ID, preserving the last 4 characters."""

    if len(value) <= 4:
        masked = "*" * len(value)
    else:
        masked = "*" * (len(value) - 4) + value[-4:]

    return MaskableTaxId(masked, is_masked=True)


def is_masked_tax_id(value: object) -> bool:
    """Return whether a value is a masked tax identifier string."""

    return isinstance(value, MaskableTaxId) and value.is_masked
