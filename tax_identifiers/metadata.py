from pydantic import ConfigDict

from tax_identifiers.base import BaseModel


class TaxIdentifierMetadata(BaseModel):
    """Base for country-specific resolved tax identifier metadata."""

    model_config = ConfigDict(extra="allow")
