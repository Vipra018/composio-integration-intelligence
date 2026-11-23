"""
Integration Intelligence - Application Metadata Schema.

Defines the structure for input applications in the benchmark dataset.
"""

from typing import List
from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator


class AppMetadata(BaseModel):
    """Metadata representing an input SaaS application to be investigated."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    id: str = Field(
        ...,
        description="Unique kebab-case identifier slug for the application (e.g., 'salesforce', 'notion').",
        pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$",
        examples=["hubspot", "salesforce", "github"],
    )
    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Official brand name of the SaaS application.",
        examples=["HubSpot", "Salesforce", "GitHub"],
    )
    category: str = Field(
        ...,
        min_length=2,
        max_length=100,
        description="High-level industry or operational category.",
        examples=["CRM & Sales", "Developer Tools & Infrastructure"],
    )
    website: HttpUrl = Field(
        ...,
        description="Canonical public homepage URL of the service.",
    )
    documentation_url: HttpUrl = Field(
        ...,
        description="Official API reference, developer documentation, or developer portal URL.",
    )
    description: str = Field(
        ...,
        min_length=10,
        max_length=500,
        description="Clear, objective one-line summary of what the software does.",
    )
    target_use_cases: List[str] = Field(
        default_factory=list,
        description="Key agentic workflow actions or tool use cases envisioned for this application.",
    )

    @field_validator("id")
    @classmethod
    def validate_id_lowercase(cls, value: str) -> str:
        if value != value.lower():
            raise ValueError(f"Application id must be strictly lowercase: '{value}'")
        return value
