import pytest
from pydantic import ValidationError

from tax_validation import BaseModel, Country, UnknownCountryError


class CountryHolder(BaseModel):
    """Test model with a single country field."""

    country: Country


class TestCountryFromString:
    """Tests for normalizing country strings to Country members."""

    @pytest.mark.parametrize(
        "value",
        ["US", "us", "  US  ", "United States", "United States of America", "USA"],
        ids=["alpha2", "lowercase", "padded", "name", "official_name", "alpha3"],
    )
    def test_resolves_united_states_forms(self, value: str) -> None:
        """Test that the various United States forms resolve to Country.US."""

        assert Country.from_string(value) == Country.US

    @pytest.mark.parametrize(
        ("value", "expected"),
        [("Germany", Country.DE), ("DE", Country.DE), ("United Kingdom", Country.GB)],
        ids=["name", "alpha2", "uk_name"],
    )
    def test_resolves_other_countries(self, value: str, expected: Country) -> None:
        """Test that non-US country names and codes resolve to their member."""

        assert Country.from_string(value) == expected

    @pytest.mark.parametrize(
        "value",
        ["", "   ", "Notacountry", "XX"],
        ids=["empty", "whitespace", "unknown_name", "unknown_code"],
    )
    def test_rejects_unknown_country(self, value: str) -> None:
        """Test that an unresolvable country string raises UnknownCountryError."""

        with pytest.raises(UnknownCountryError):
            Country.from_string(value)

    def test_value_is_uppercase_iso_code(self) -> None:
        """Test that a country's value is its uppercase ISO alpha-2 code."""

        assert Country.US.value == "US"
        assert str(Country.US) == "US"


class TestCountryFieldCoercion:
    """Tests for coercing raw country strings on model fields."""

    @pytest.mark.parametrize(
        ("value", "expected"),
        [("United States", Country.US), ("us", Country.US), ("France", Country.FR)],
        ids=["name", "lowercase_code", "other_name"],
    )
    def test_coerces_raw_country_strings(self, value: str, expected: Country) -> None:
        """Test that a country field accepts raw strings such as DB column values."""

        assert CountryHolder(country=value).country == expected

    def test_rejects_unknown_country_string(self) -> None:
        """Test that an unresolvable country string fails field validation."""

        with pytest.raises(ValidationError):
            CountryHolder(country="Notacountry")
