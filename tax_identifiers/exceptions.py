from typing import Final


class TaxValidationError(ValueError):
    """Base error for tax identifier validation failures."""


class InvalidTaxIdError(TaxValidationError):
    """Raised when a tax identifier does not conform to its country's structural rules."""


class UnsupportedTaxIdTypeError(TaxValidationError):
    """Raised when a validator receives a tax identifier type it does not handle."""


class UnknownCountryError(TaxValidationError):
    """Raised when a country string cannot be resolved to a known country."""


INVALID_TAX_ID_MESSAGE: Final[str] = "{tax_id_type} value is not a valid {country} tax identifier"
