from tax_validation.countries import Country
from tax_validation.enums import TaxIdentifierType
from tax_validation.exceptions import InvalidTaxIdError, UnsupportedTaxIdTypeError
from tax_validation.models import TaxValidationResult
from tax_validation.rules import get_country_rules


class TaxValidator:
    """Validate tax identifiers for a country and resolve their metadata."""

    def __init__(self, country: Country = Country.US):
        """Resolve the tax rules for the given country."""

        self._rules = get_country_rules(country)

    @property
    def country(self) -> Country:
        """Return the country this validator handles."""

        return self._rules.country

    def validate(self, tax_id: str, tax_id_type: TaxIdentifierType) -> TaxValidationResult:
        """Validate a tax identifier, raising when it is unsupported or structurally invalid."""

        if tax_id_type not in self._rules.supported_types:
            raise UnsupportedTaxIdTypeError(f"{self.country} does not handle {tax_id_type}")

        result = TaxValidationResult.from_tax_identifier(
            country=self.country,
            tax_id=tax_id,
            tax_id_type=tax_id_type,
        )

        if result is None:
            raise InvalidTaxIdError(f"{tax_id_type} value is not a valid {self.country} tax identifier")

        return result
