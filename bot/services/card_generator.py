"""
Card generator service for Discord digest images.

Generates PNG images from digest data using HTML templates and html2image.
Includes auto-cropping to remove white space.
"""

import io
import logging
import tempfile
from pathlib import Path
from typing import Any

from html2image import Html2Image
from jinja2 import Environment, FileSystemLoader
from PIL import Image

logger = logging.getLogger(__name__)

# Template directory
TEMPLATES_DIR = Path(__file__).parent.parent / "templates"

# Discord recommended dimensions
DISCORD_MAX_WIDTH = 1200
DISCORD_EMBED_WIDTH = 800  # Optimal for embed display


class CardGenerator:
    """Generates digest card images from HTML templates."""

    def __init__(self):
        """Initialize the card generator with Jinja2 environment."""
        self.jinja_env = Environment(
            loader=FileSystemLoader(TEMPLATES_DIR),
            autoescape=True,
        )
        self._hti: Html2Image | None = None

    def _get_hti(self, width: int = 900, height: int = 2000) -> Html2Image:
        """Get Html2Image instance with specified size.

        Args:
            width: Viewport width
            height: Viewport height (set large to capture full content)

        Returns:
            Configured Html2Image instance
        """
        hti = Html2Image(
            output_path=tempfile.gettempdir(),
            size=(width, height),
        )
        # IMPORTANT: Include --hide-scrollbars and --default-background-color
        hti.browser.flags = [
            "--no-sandbox",
            "--disable-gpu",
            "--disable-dev-shm-usage",
            "--disable-software-rasterizer",
            "--hide-scrollbars",  # Hide scrollbars
            "--default-background-color=0f0f1a",  # Match our dark background
            "--force-device-scale-factor=1",
        ]
        return hti

    def generate_daily_card(self, content: dict[str, Any], digest_date: str) -> bytes:
        """Generate a daily digest card image.

        Args:
            content: The digest content with headlines, research, industry, watching, metadata
            digest_date: The date string for the digest (e.g., "2025-12-26")

        Returns:
            PNG image as bytes (auto-cropped)
        """
        # Prepare template data
        headlines = content.get("headlines", [])
        research = content.get("research", [])
        industry = content.get("industry", [])
        watching = content.get("watching", [])
        metadata = content.get("metadata", {})

        # Extract unique sources from articles
        sources = self._extract_sources(content)

        template_data = {
            "date": self._format_date(digest_date),
            "headlines": headlines,
            "research": research,
            "industry": industry,
            "watching": watching,
            "sources_count": len(sources),
            "sources_list": " • ".join(sources),
            "stats": {
                "analyzed": metadata.get("articles_analyzed", 0),
                "selected": metadata.get("selected_count", len(headlines) + len(research) + len(industry) + len(watching)),
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
        theme: str | None = None,
    ) -> bytes:
        """Generate a weekly digest card image.

        Args:
            content: The weekly digest content (trends, top_stories, summary, metadata)
            week_start: Start date string
            week_end: End date string
            theme: Optional theme for thematic digests

        Returns:
            PNG image as bytes (auto-cropped)
        """
        trends = content.get("trends", [])
        top_stories = content.get("top_stories", [])
        metadata = content.get("metadata", {})

        # Calculate days in range
        from datetime import datetime
        try:
            start = datetime.strptime(week_start, "%Y-%m-%d")
            end = datetime.strptime(week_end, "%Y-%m-%d")
            days = (end - start).days + 1
        except (ValueError, TypeError):
            days = 7

        # Get top story with proper source extraction
        top_story = None
        if top_stories:
            story = top_stories[0]
            url = story.get("url", "")
            source = story.get("source", "")
            if not source and url:
                try:
                    source = url.split("/")[2].replace("www.", "")
                except (IndexError, AttributeError):
                    source = ""
            top_story = {
                "title": story.get("title", ""),
                "summary": story.get("summary", ""),
                "source": source,
            }

        # Format trends for template
        formatted_trends = []
        for trend in trends[:6]:
            formatted_trends.append({
                "name": trend.get("name", ""),
                "direction": trend.get("direction", "stable"),
            })

        template_data = {
            "date_range": f"{self._format_date(week_start)} → {self._format_date(week_end)}",
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

        template = self.jinja_env.get_template("digest_card_weekly.html")
        html_content = template.render(**template_data)

        return self._render_html_to_image(html_content, "weekly_digest")

    def _extract_sources(self, content: dict[str, Any]) -> list[str]:
        """Extract unique source names from digest content.

        Args:
            content: The digest content

        Returns:
            List of unique source names
        """
        sources = set()

        for category in ["headlines", "research", "industry", "watching"]:
            for item in content.get(category, []):
                source = item.get("source", "")
                if source:
                    sources.add(source)

        # Add standard sources if we have few
        standard_sources = ["TechCrunch", "OpenAI", "Google AI", "HuggingFace", "arXiv",
                          "Reddit", "Hacker News", "The Verge", "Ars Technica"]

        # Ensure we have at least the standard count shown
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
            PNG image as bytes (auto-cropped to remove white/dark space)
        """
        import uuid

        # Generate unique filename
        filename = f"{filename_prefix}_{uuid.uuid4().hex[:8]}.png"
        image_path = Path(tempfile.gettempdir()) / filename

        try:
            # Use large height to capture full content
            hti = self._get_hti(width=900, height=2500)

            # Capture screenshot
            hti.screenshot(
                html_str=html_content,
                save_as=filename,
            )

            # Auto-crop the image to remove empty space
            image_bytes = self._auto_crop_image(image_path)

            # Cleanup
            image_path.unlink(missing_ok=True)

            logger.info("Generated card image: %d bytes", len(image_bytes))
            return image_bytes

        except Exception as e:
            logger.error("Failed to generate card image: %s", e)
            # Cleanup on error
            image_path.unlink(missing_ok=True)
            raise

    def _auto_crop_image(self, image_path: Path) -> bytes:
        """Auto-crop an image to remove empty space at the bottom.

        Detects the background color and crops to content boundaries.

        Args:
            image_path: Path to the PNG image

        Returns:
            Cropped PNG image as bytes
        """
        with Image.open(image_path) as img:
            # Convert to RGB if needed
            if img.mode != 'RGB':
                img = img.convert('RGB')

            # Get the background color from the top-left corner
            bg_color = img.getpixel((0, 0))

            # Find the bounding box of non-background content
            # Scan from bottom to find where content ends
            width, height = img.size
            content_bottom = height

            # Scan from bottom up to find content
            tolerance = 10  # Color tolerance for matching background

            for y in range(height - 1, 0, -1):
                row_has_content = False
                # Sample pixels across the row
                for x in range(0, width, 10):
                    pixel = img.getpixel((x, y))
                    if not self._colors_similar(pixel, bg_color, tolerance):
                        row_has_content = True
                        break

                if row_has_content:
                    content_bottom = min(y + 20, height)  # Add small padding
                    break

            # Crop the image
            if content_bottom < height:
                img = img.crop((0, 0, width, content_bottom))
                logger.info("Auto-cropped image from %d to %d pixels height", height, content_bottom)

            # Save to bytes
            buffer = io.BytesIO()
            img.save(buffer, format='PNG', optimize=True)
            return buffer.getvalue()

    def _colors_similar(self, color1: tuple, color2: tuple, tolerance: int) -> bool:
        """Check if two RGB colors are similar within tolerance.

        Args:
            color1: First RGB color tuple
            color2: Second RGB color tuple
            tolerance: Maximum difference per channel

        Returns:
            True if colors are similar
        """
        return all(abs(c1 - c2) <= tolerance for c1, c2 in zip(color1, color2))

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
    import asyncio
    from functools import partial

    generator = get_card_generator()

    loop = asyncio.get_event_loop()
    func = partial(generator.generate_weekly_card, content, week_start, week_end, theme)
    return await loop.run_in_executor(None, func)
