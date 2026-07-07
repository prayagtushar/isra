from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, HttpUrl, field_validator

class Startup(BaseModel):
    

    model_config = {"frozen": True}

    name: str = Field(..., description="Display Name")
    normalized_name: str = Field(..., description="lowercase, alphanumeric")
    one_liner: Optional[str] = Field(None, description="One liner about the company")
    description: str = Field(
        ..., description="long description about the startup", min_length=5
    )
    founders: List[str] = Field(..., description="Founders List", min_length=1)
    founded_year: Optional[int] = Field(None, ge=1900, le=2100)
    headquarters: Optional[str] = None
    fundings: Optional[float] = None
    sectors: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)

    source_url: HttpUrl = Field(
        ..., description="URL from where this record was fetched"
    )
    scraped_date: Optional[datetime] = Field(
        None, description="Date and Time of scraping"
    )

    def __hash__(self) -> int:
        return hash(self.normalized_name)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Startup):
            return NotImplemented
        return self.normalized_name == other.normalized_name

    @field_validator("normalized_name")
    @classmethod
    def normalize(cls, name: str) -> str:
        return "".join(char.lower() for char in name if char.isalnum())
