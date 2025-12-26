"""
Card generator service for Discord digest images.

Generates PNG images from digest data using HTML templates and html2image.
Includes auto-cropping to remove white space.
"""

import asyncio
import io
import logging
import tempfile
import uuid
from functools import partial
from pathlib import Path
from typing import Any

from html2image import Html2Image
from jinja2 import Environment, FileSystemLoader
from PIL import Image

from services.utils.date_utils import calculate_days_in_range, format_date_display

logger = logging.getLogger(__name__)

# Template directory
TEMPLATES_DIR = Path(__file__).parent.parent / "templates"

# Discord recommended dimensions
DISCORD_MAX_WIDTH = 1200
DISCORD_EMBED_WIDTH = 800  # Optimal for embed display

# Browser flags for html2image
BROWSER_FLAGS = [
    "--no-sandbox",
    "--disable-gpu",
    "--disable-dev-shm-usage",
    "--disable-software-rasterizer",
    "--hide-scrollbars",
    "--default-background-color=0f0f1a",
    "--force-device-scale-factor=1",
]


class ImageRenderer:
    """Handles HTML to image rendering and cropping."""

    @staticmethod
    def create_hti(width: int = 900, height: int = 2500) -> Html2Image:
        """Create Html2Image instance with specified size.

        Args:
            width: Viewport width
            height: Viewport height

        Returns:
            Configured Html2Image instance
        """
        hti = Html2Image(
            output_path=tempfile.gettempdir(),
            size=(width, height),
        )
        hti.browser.flags = BROWSER_FLAGS
        return hti

    @staticmethod
    def render_to_file(hti: Html2Image, html_content: str, filename: str) -> Path:
        """Render HTML content to a temporary file.

        Args:
            hti: Html2Image instance
            html_content: HTML to render
            filename: Output filename

        Returns:
            Path to rendered image
        """
        hti.screenshot(html_str=html_content, save_as=filename)
        return Path(tempfile.gettempdir()) / filename

    @staticmethod
    def auto_crop(image_path: Path, tolerance: int = 10) -> bytes:
        """Auto-crop image to remove empty space at the bottom.

        Args:
            image_path: Path to the PNG image
            tolerance: Color tolerance for matching background

        Returns:
            Cropped PNG image as bytes
        """
        with Image.open(image_path) as img:
            if img.mode != 'RGB':
                img = img.convert('RGB')

            bg_color = img.getpixel((0, 0))
            width, height = img.size
            content_bottom = height

            # Scan from bottom up to find content
            for y in range(height - 1, 0, -1):
                row_has_content = False
                for x in range(0, width, 10):
                    pixel = img.getpixel((x, y))
                    if not ImageRenderer._colors_similar(pixel, bg_color, tolerance):
                        row_has_content = True
                        break

                if row_has_content:
                    content_bottom = min(y + 20, height)
                    break

            if content_bottom < height:
                img = img.crop((0, 0, width, content_bottom))
                logger.info("Auto-cropped from %d to %d pixels", height, content_bottom)

            buffer = io.BytesIO()
            img.save(buffer, format='PNG', optimize=True)
            return buffer.getvalue()

    @staticmethod
    def _colors_similar(color1: tuple, color2: tuple, tolerance: int) -> bool:
        """Check if two RGB colors are similar within tolerance."""
        return all(abs(c1 - c2) <= tolerance for c1, c2 in zip(color1, color2))


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
            "counts": {
                "trends": len(trends),
                "stories": len(top_stories),
            },
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

        standard_sources = [
            "TechCrunch", "OpenAI", "Google AI", "HuggingFace", "arXiv",
            "Reddit", "Hacker News", "The Verge", "Ars Technica"
        ]

        if len(sources) < 5:
            for s in standard_sources:
                sources.add(s)
                if len(sources) >= 10:
                    break

        return sorted(list(sources))[:10]

    def _render_html_to_image(self, html_content: str, filename_prefix: str) -> bytes:
        """Render HTML content to a PNG image with auto-cropping.

        Args:
            html_content: The HTML string to render
            filename_prefix: Prefix for the temporary filename

        Returns:
            PNG image as bytes
        """
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
    """Async wrapper for generating daily digest cards.

    Args:
        content: The digest content
        digest_date: The date string

    Returns:
        PNG image as bytes
    """
    generator = get_card_generator()
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
    theme: str | None = None,
) -> bytes:
    """Async wrapper for generating weekly digest cards.

    Args:
        content: The weekly digest content
        week_start: Start date string
        week_end: End date string
        theme: Optional theme for thematic digests

    Returns:
        PNG image as bytes
    """
    generator = get_card_generator()
    loop = asyncio.get_event_loop()
    func = partial(generator.generate_weekly_card, content, week_start, week_end, theme)
    return await loop.run_in_executor(None, func)
