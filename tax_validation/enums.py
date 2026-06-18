from enum import Enum


class BaseEnum(str, Enum):
    """String-valued enum base class."""

    def __str__(self) -> str:
        return self.value


class Country(BaseEnum):
    """Country a tax identifier validator handles."""

    US = "us"


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


class USState(BaseEnum):
    """US state, district, and territory postal codes."""

    ALABAMA = "AL"
    ALASKA = "AK"
    ARIZONA = "AZ"
    ARKANSAS = "AR"
    CALIFORNIA = "CA"
    COLORADO = "CO"
    CONNECTICUT = "CT"
    DELAWARE = "DE"
    DISTRICT_OF_COLUMBIA = "DC"
    FLORIDA = "FL"
    GEORGIA = "GA"
    HAWAII = "HI"
    IDAHO = "ID"
    ILLINOIS = "IL"
    INDIANA = "IN"
    IOWA = "IA"
    KANSAS = "KS"
    KENTUCKY = "KY"
    LOUISIANA = "LA"
    MAINE = "ME"
    MARYLAND = "MD"
    MASSACHUSETTS = "MA"
    MICHIGAN = "MI"
    MINNESOTA = "MN"
    MISSISSIPPI = "MS"
    MISSOURI = "MO"
    MONTANA = "MT"
    NEBRASKA = "NE"
    NEVADA = "NV"
    NEW_HAMPSHIRE = "NH"
    NEW_JERSEY = "NJ"
    NEW_MEXICO = "NM"
    NEW_YORK = "NY"
    NORTH_CAROLINA = "NC"
    NORTH_DAKOTA = "ND"
    OHIO = "OH"
    OKLAHOMA = "OK"
    OREGON = "OR"
    PENNSYLVANIA = "PA"
    RHODE_ISLAND = "RI"
    SOUTH_CAROLINA = "SC"
    SOUTH_DAKOTA = "SD"
    TENNESSEE = "TN"
    TEXAS = "TX"
    UTAH = "UT"
    VERMONT = "VT"
    VIRGINIA = "VA"
    WASHINGTON = "WA"
    WEST_VIRGINIA = "WV"
    WISCONSIN = "WI"
    WYOMING = "WY"
    AMERICAN_SAMOA = "AS"
    GUAM = "GU"
    NORTHERN_MARIANA_ISLANDS = "MP"
    PUERTO_RICO = "PR"
    US_VIRGIN_ISLANDS = "VI"
