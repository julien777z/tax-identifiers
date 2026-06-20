from pydantic import ConfigDict, model_validator
from pydantic_super_model import SuperModelPydanticMixin

from tax_identifiers.normalization import empty_str_to_none


class BaseModel(SuperModelPydanticMixin):
    """Base model with annotation scanning and string normalization."""

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        str_strip_whitespace=True,
    )

    @model_validator(mode="before")
    @classmethod
    def empty_strings_to_none(cls, data: object) -> object:
        """Convert empty-string inputs to None before field validation."""

        if isinstance(data, dict):
            return empty_str_to_none(data)

        return data
