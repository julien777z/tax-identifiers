from typing import Annotated

from pydantic import BeforeValidator

from tax_identifiers.us.enums import USState
from tax_identifiers.us.transformers import transform_us_state

USStateField = Annotated[USState, "us_state", BeforeValidator(transform_us_state)]
