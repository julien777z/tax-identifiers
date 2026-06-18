from tax_validation.enums import Country, TaxIdentifierType
from tax_validation.exceptions import InvalidTaxIdError, UnsupportedTaxIdTypeError
from tax_validation.us.models import SSNValidation, TinValidation
from tax_validation.us.tax_identifiers import is_us_tax_identifier_type
from tax_validation.validators import TaxValidator


class USTaxValidator(TaxValidator[TinValidation]):
    """United States tax identifier validator (SSN, EIN, ITIN)."""

    @property
    def country(self) -> Country:
        """Return the country this validator handles."""

        return Country.US

    def validate(self, tax_id: str, tax_id_type: TaxIdentifierType) -> TinValidation:
        """Validate a US tax identifier, raising when it is structurally invalid."""

        if not is_us_tax_identifier_type(tax_id_type):
            raise UnsupportedTaxIdTypeError(f"USTaxValidator does not handle {tax_id_type}")

        validation = TinValidation.from_tax_identifier(tax_id=tax_id, tax_id_type=tax_id_type)

        if validation is None:
            raise InvalidTaxIdError(f"{tax_id_type} value is not a valid US tax identifier")

        return validation

    def resolve_ssn(self, ssn: str) -> SSNValidation | None:
        """Resolve issuing state and issued years for an SSN, or None when not resolvable."""

        return SSNValidation.from_tax_identifier(ssn)
