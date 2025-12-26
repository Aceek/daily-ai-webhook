"""
Card generator service for Discord digest images.

Generates PNG images from digest data using HTML templates and html2image.
"""

import asyncio
import logging
import tempfile
import uuid
from functools import partial
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader

from services.image_renderer import ImageRenderer
from services.utils.date_utils import calculate_days_in_range, format_date_display

logger = logging.getLogger(__name__)

# Template directory
TEMPLATES_DIR = Path(__file__).parent.parent / "templates"

# Standard sources for fallback
STANDARD_SOURCES = [
    "TechCrunch", "OpenAI", "Google AI", "HuggingFace", "arXiv",
    "Reddit", "Hacker News", "The Verge", "Ars Technica"
]


class CardGenerator:
    """Generates digest card images from HTML templates."""

    def __init__(self) -> None:
        """Initialize the card generator with Jinja2 environment."""
        self.jinja_env = Environment(
            loader=FileSystemLoader(TEMPLATES_DIR),
            autoescape=True,
        )
        self.renderer = ImageRenderer()

    def generate_daily_card(self, content: dict[str, Any], digest_date: str) -> bytes:
        """Generate a daily digest card image.

        Args:
            content: The digest content
            digest_date: The date string (YYYY-MM-DD)

        Returns:
            PNG image as bytes
        """
        template_data = self._prepare_daily_data(content, digest_date)
        template = self.jinja_env.get_template("digest_card.html")
        html_content = template.render(**template_data)
        return self._render_html_to_image(html_content, "daily_digest")

    def generate_weekly_card(
        self,
        content: dict[str, Any],
        week_start: str,
        week_end: str,
        theme: str | None = None,
    ) -> bytes:
        """Generate a weekly digest card image.

        Args:
            content: The weekly digest content
            week_start: Start date string
            week_end: End date string
            theme: Optional theme for thematic digests

        Returns:
            PNG image as bytes
        """
        template_data = self._prepare_weekly_data(content, week_start, week_end, theme)
        template = self.jinja_env.get_template("digest_card_weekly.html")
        html_content = template.render(**template_data)
        return self._render_html_to_image(html_content, "weekly_digest")

    def _prepare_daily_data(self, content: dict[str, Any], digest_date: str) -> dict:
        """Prepare template data for daily digest."""
        headlines = content.get("headlines", [])
        research = content.get("research", [])
        industry = content.get("industry", [])
        watching = content.get("watching", [])
        metadata = content.get("metadata", {})

        sources = self._extract_sources(content)
        total_selected = len(headlines) + len(research) + len(industry) + len(watching)

        return {
            "date": format_date_display(digest_date),
            "headlines": headlines,
            "research": research,
            "industry": industry,
            "watching": watching,
            "sources_count": len(sources),
            "sources_list": " - ".join(sources),
            "stats": {
                "analyzed": metadata.get("articles_analyzed", 0),
                "selected": metadata.get("selected_count", total_selected),
                "searches": metadata.get("web_searches", 0),
                "fact_checks": metadata.get("fact_checks", 0),
            },
            "counts": {
                "headlines": len(headlines),
                "research": len(research),
                "industry": len(industry),
                "watching": len(watching),
            },
            "top_story": headlines[0] if headlines else None,
        }

    def _prepare_weekly_data(
        self, content: dict[str, Any], week_start: str, week_end: str, theme: str | None
    ) -> dict:
        """Prepare template data for weekly digest."""
        trends = content.get("trends", [])
        top_stories = content.get("top_stories", [])
        metadata = content.get("metadata", {})

        days = calculate_days_in_range(week_start, week_end)
        top_story = self._extract_top_story(top_stories)

        formatted_trends = [
            {"name": t.get("name", ""), "direction": t.get("direction", "stable")}
            for t in trends[:6]
        ]

        return {
            "date_range": f"{format_date_display(week_start)} -> {format_date_display(week_end)}",
            "theme": theme,
            "stats": {
                "days": days,
                "analyzed": metadata.get("articles_analyzed", 0),
                "top_stories": len(top_stories),
            },
            "counts": {"trends": len(trends), "stories": len(top_stories)},
            "top_story": top_story,
            "trends": formatted_trends,
        }

    def _extract_top_story(self, top_stories: list[dict]) -> dict | None:
        """Extract and format top story with source."""
        if not top_stories:
            return None

        story = top_stories[0]
        url = story.get("url", "")
        source = story.get("source", "")

        if not source and url:
            try:
                source = url.split("/")[2].replace("www.", "")
            except (IndexError, AttributeError):
                source = ""

        return {
            "title": story.get("title", ""),
            "summary": story.get("summary", ""),
            "source": source,
        }

    def _extract_sources(self, content: dict[str, Any]) -> list[str]:
        """Extract unique source names from digest content."""
        sources = set()

        for category in ["headlines", "research", "industry", "watching"]:
            for item in content.get(category, []):
                source = item.get("source", "")
                if source:
                    sources.add(source)

        if len(sources) < 5:
            for s in STANDARD_SOURCES:
                sources.add(s)
                if len(sources) >= 10:
                    break

        return sorted(list(sources))[:10]

    def _render_html_to_image(self, html_content: str, filename_prefix: str) -> bytes:
        """Render HTML content to a PNG image with auto-cropping."""
        filename = f"{filename_prefix}_{uuid.uuid4().hex[:8]}.png"
        image_path = Path(tempfile.gettempdir()) / filename

        try:
            hti = self.renderer.create_hti()
            self.renderer.render_to_file(hti, html_content, filename)
            image_bytes = self.renderer.auto_crop(image_path)
            logger.info("Generated card image: %d bytes", len(image_bytes))
            return image_bytes
        finally:
            image_path.unlink(missing_ok=True)


# Singleton instance
_card_generator: CardGenerator | None = None


def get_card_generator() -> CardGenerator:
    """Get the singleton CardGenerator instance."""
    global _card_generator
    if _card_generator is None:
        _card_generator = CardGenerator()
    return _card_generator


async def generate_daily_card_async(content: dict[str, Any], digest_date: str) -> bytes:
    """Async wrapper for generating daily digest cards."""
    generator = get_card_generator()
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, generator.generate_daily_card, content, digest_date)


async def generate_weekly_card_async(
    content: dict[str, Any],
    week_start: str,
    week_end: str,
    theme: str | None = None,
) -> bytes:
    """Async wrapper for generating weekly digest cards."""
    generator = get_card_generator()
    loop = asyncio.get_event_loop()
    func = partial(generator.generate_weekly_card, content, week_start, week_end, theme)
    return await loop.run_in_executor(None, func)
