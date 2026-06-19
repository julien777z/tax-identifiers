class TaxValidationError(Exception):
    """Base error for tax identifier validation failures."""


class InvalidTaxIdError(TaxValidationError):
    """Raised when a tax identifier does not conform to its country's structural rules."""


class UnsupportedTaxIdTypeError(TaxValidationError):
    """Raised when a validator receives a tax identifier type it does not handle."""


class UnknownCountryError(TaxValidationError, ValueError):
    """Raised when a country string cannot be resolved to a known country."""
