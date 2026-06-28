# app/schemas.py
from pydantic import BaseModel, Field
from typing import Literal

class SourceSummary(BaseModel):
    source: str = Field(description="URL, filename, or topic identifier")
    source_type: Literal["web", "pdf", "memory"]
    summary: str = Field(description="Brief summary of what this source contributed")

class ResearchOutput(BaseModel):
    query: str = Field(description="The original user question")
    sources_used: list[SourceSummary] = Field(description="All sources consulted during research")
    synthesis: str = Field(description="Final synthesized answer combining all sources")
    confidence: Literal["low", "medium", "high"] = Field(description="Confidence in the synthesis based on source quality and agreement")