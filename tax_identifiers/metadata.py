from pydantic import ConfigDict

from tax_identifiers.base import BaseModel


class TaxIdentifierMetadata(BaseModel):
    """Base for country-specific resolved tax identifier metadata."""

    # Country-specific subclasses carry their own fields. Allow extras so a value
    # serialized from a concrete subclass survives re-validation against this base
    # (e.g. a FastAPI response_model dump -> validate -> dump cycle) instead of
    # collapsing to an empty object.
    model_config = ConfigDict(extra="allow")
