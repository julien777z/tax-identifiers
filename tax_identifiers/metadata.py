from pydantic import ConfigDict

from tax_identifiers.base import BaseModel


class TaxIdentifierMetadata(BaseModel):
    """Base for country-specific resolved tax identifier metadata."""

    # Allow extras so concrete subclass fields survive re-validation against this
    # empty base (e.g. FastAPI's response_model dump -> validate -> dump).
    model_config = ConfigDict(extra="allow")
