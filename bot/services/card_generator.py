"""
Card generator service for Discord digest images.

Generates PNG images from digest data using HTML templates and html2image.
"""

import io
import logging
import tempfile
from pathlib import Path
from typing import Any

from html2image import Html2Image
from jinja2 import Environment, FileSystemLoader

logger = logging.getLogger(__name__)

# Template directory
TEMPLATES_DIR = Path(__file__).parent.parent / "templates"


class CardGenerator:
    """Generates digest card images from HTML templates."""

    def __init__(self):
        """Initialize the card generator with Jinja2 environment."""
        self.jinja_env = Environment(
            loader=FileSystemLoader(TEMPLATES_DIR),
            autoescape=True,
        )
        self._hti: Html2Image | None = None

    @property
    def hti(self) -> Html2Image:
        """Lazy-load Html2Image instance."""
        if self._hti is None:
            # Use temp directory for output
            self._hti = Html2Image(
                output_path=tempfile.gettempdir(),
                size=(1200, 800),  # Will be adjusted by content
            )
            # Disable sandbox for Docker compatibility
            self._hti.browser.flags = [
                "--no-sandbox",
                "--disable-gpu",
                "--disable-dev-shm-usage",
                "--disable-software-rasterizer",
            ]
        return self._hti

    def generate_daily_card(self, content: dict[str, Any], digest_date: str) -> bytes:
        """Generate a daily digest card image.

        Args:
            content: The digest content with headlines, research, industry, watching, metadata
            digest_date: The date string for the digest (e.g., "2025-12-26")

        Returns:
            PNG image as bytes
        """
        # Prepare template data
        headlines = content.get("headlines", [])
        metadata = content.get("metadata", {})

        template_data = {
            "date": self._format_date(digest_date),
            "headlines": headlines,
            "stats": {
                "analyzed": metadata.get("articles_analyzed", 0),
                "selected": metadata.get("selected_count", len(headlines)),
                "searches": metadata.get("web_searches", 0),
                "fact_checks": metadata.get("fact_checks", 0),
            },
            "counts": {
                "research": len(content.get("research", [])),
                "industry": len(content.get("industry", [])),
                "watching": len(content.get("watching", [])),
            },
        }

        # Render template
        template = self.jinja_env.get_template("digest_card.html")
        html_content = template.render(**template_data)

        # Generate image
        return self._render_html_to_image(html_content, "daily_digest")

    def generate_weekly_card(
        self,
        content: dict[str, Any],
        week_start: str,
        week_end: str,
    ) -> bytes:
        """Generate a weekly digest card image.

        Args:
            content: The weekly digest content
            week_start: Start date string
            week_end: End date string

        Returns:
            PNG image as bytes
        """
        # For now, reuse the daily template with adapted data
        # TODO: Create a dedicated weekly template if needed
        trends = content.get("trends", [])
        top_stories = content.get("top_stories", [])
        metadata = content.get("metadata", {})

        # Convert top stories to headline format for the template
        headlines = []
        for story in top_stories[:4]:
            headlines.append({
                "emoji": story.get("emoji", "🏆"),
                "title": story.get("title", ""),
                "summary": story.get("summary", ""),
                "source": story.get("url", "").split("/")[2] if story.get("url") else "",
                "confidence": "high",
                "importance": "major",
            })

        template_data = {
            "date": f"{self._format_date(week_start)} → {self._format_date(week_end)}",
            "headlines": headlines,
            "stats": {
                "analyzed": metadata.get("articles_analyzed", 0),
                "selected": len(top_stories),
                "searches": 0,
                "fact_checks": 0,
            },
            "counts": {
                "research": 0,
                "industry": 0,
                "watching": len(trends),
            },
        }

        template = self.jinja_env.get_template("digest_card.html")
        html_content = template.render(**template_data)

        return self._render_html_to_image(html_content, "weekly_digest")

    def _render_html_to_image(self, html_content: str, filename_prefix: str) -> bytes:
        """Render HTML content to a PNG image.

        Args:
            html_content: The HTML string to render
            filename_prefix: Prefix for the temporary filename

        Returns:
            PNG image as bytes
        """
        import uuid

        # Generate unique filename
        filename = f"{filename_prefix}_{uuid.uuid4().hex[:8]}.png"

        try:
            # Capture screenshot
            self.hti.screenshot(
                html_str=html_content,
                save_as=filename,
            )

            # Read the generated image
            image_path = Path(tempfile.gettempdir()) / filename
            with open(image_path, "rb") as f:
                image_bytes = f.read()

            # Cleanup
            image_path.unlink(missing_ok=True)

            logger.info("Generated card image: %d bytes", len(image_bytes))
            return image_bytes

        except Exception as e:
            logger.error("Failed to generate card image: %s", e)
            raise

    def _format_date(self, date_str: str) -> str:
        """Format a date string for display.

        Args:
            date_str: Date in YYYY-MM-DD format

        Returns:
            Formatted date string (e.g., "December 26, 2025")
        """
        from datetime import datetime

        try:
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
            return date_obj.strftime("%B %d, %Y")
        except (ValueError, TypeError):
            return date_str


# Singleton instance
_card_generator: CardGenerator | None = None


def get_card_generator() -> CardGenerator:
    """Get the singleton CardGenerator instance."""
    global _card_generator
    if _card_generator is None:
        _card_generator = CardGenerator()
    return _card_generator


async def generate_daily_card_async(
    content: dict[str, Any],
    digest_date: str,
) -> bytes:
    """Async wrapper for generating daily digest cards.

    Args:
        content: The digest content
        digest_date: The date string

    Returns:
        PNG image as bytes
    """
    import asyncio

    generator = get_card_generator()

    # Run in executor to avoid blocking
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None,
        generator.generate_daily_card,
        content,
        digest_date,
    )


async def generate_weekly_card_async(
    content: dict[str, Any],
    week_start: str,
    week_end: str,
) -> bytes:
    """Async wrapper for generating weekly digest cards.

    Args:
        content: The weekly digest content
        week_start: Start date string
        week_end: End date string

    Returns:
        PNG image as bytes
    """
    import asyncio

    generator = get_card_generator()

    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None,
        generator.generate_weekly_card,
        content,
        week_start,
        week_end,
    )
