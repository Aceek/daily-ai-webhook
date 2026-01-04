"""Shared models for the entire application."""

from pydantic import BaseModel, Field


class ArticleInput(BaseModel):
    """Article received from RSS/API input."""

    title: str
    url: str
    source: str = ""
    description: str = ""
    pub_date: str = ""


class NewsItem(BaseModel):
    """Article selected for digest publication."""

    title: str = Field(..., description="Article title")
    summary: str = Field(..., description="Brief summary")
    url: str = Field(..., description="Article URL")
    source: str = Field(..., description="Source name")
    category: str = Field(..., description="Assigned category")
    confidence: float = Field(..., ge=0, le=1, description="Confidence score 0-1")
    relevance_score: int | None = Field(
        None, ge=1, le=10, description="Relevance 1-10"
    )


class ExcludedItem(BaseModel):
    """Article excluded from digest."""

    url: str = Field(..., description="Article URL")
    title: str = Field(..., description="Article title")
    category: str = Field(..., description="Assigned category")
    reason: str = Field(
        ...,
        description="Exclusion reason: off_topic|duplicate|low_priority|outdated",
    )
    score: int = Field(..., ge=1, le=10, description="Relevance score 1-10")
    source: str | None = Field(None, description="Source name")


class ArticleLog(BaseModel):
    """Article data for logging purposes."""

    title: str
    url: str
    source: str
    pub_date: str = ""
    description_preview: str = Field(default="", description="First 100 chars")

    @classmethod
    def from_input(cls, article: "ArticleInput") -> "ArticleLog":
        """Create ArticleLog from ArticleInput."""
        return cls(
            title=article.title,
            url=article.url,
            source=article.source,
            pub_date=article.pub_date,
            description_preview=(
                article.description[:100] if article.description else ""
            ),
        )
