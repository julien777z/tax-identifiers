from enum import Enum


class BaseEnum(str, Enum):
    """String-valued enum base class."""

    def __str__(self) -> str:
        return self.value


class TaxIdentifierType(BaseEnum):
    """Type of a tax identifier."""

    SSN = "ssn"
    EIN = "ein"
    ITIN = "itin"
    US_UNSPECIFIED = "us_unspecified"
    FOREIGN_TIN = "foreign_tin"
    NONE = "none"


class TaxIdentifierOrigin(BaseEnum):
    """Origin of a tax identifier (US versus foreign)."""

    US_TIN = "us_tin"
    FOREIGN_TIN = "foreign_tin"


class TinType(BaseEnum):
    """TIN subtype metadata for tax identifiers."""

    EIN = "ein"
    SSN = "ssn"
    TIN = "tin"
    OTHER = "other"
