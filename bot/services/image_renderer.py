"""
Image renderer for HTML to PNG conversion.

Handles HTML to image rendering and auto-cropping functionality.
"""

import io
import logging
import tempfile
from pathlib import Path

from html2image import Html2Image
from PIL import Image

logger = logging.getLogger(__name__)

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
            content_bottom = ImageRenderer._find_content_bottom(img, bg_color, tolerance)

            if content_bottom < height:
                img = img.crop((0, 0, width, content_bottom))
                logger.info("Auto-cropped from %d to %d pixels", height, content_bottom)

            buffer = io.BytesIO()
            img.save(buffer, format='PNG', optimize=True)
            return buffer.getvalue()

    @staticmethod
    def _find_content_bottom(img: Image.Image, bg_color: tuple, tolerance: int) -> int:
        """Find the bottom of content by scanning from bottom up.

        Args:
            img: PIL Image
            bg_color: Background color tuple
            tolerance: Color matching tolerance

        Returns:
            Y coordinate of content bottom with padding
        """
        width, height = img.size

        for y in range(height - 1, 0, -1):
            for x in range(0, width, 10):
                pixel = img.getpixel((x, y))
                if not ImageRenderer._colors_similar(pixel, bg_color, tolerance):
                    return min(y + 20, height)

        return height

    @staticmethod
    def _colors_similar(color1: tuple, color2: tuple, tolerance: int) -> bool:
        """Check if two RGB colors are similar within tolerance."""
        return all(abs(c1 - c2) <= tolerance for c1, c2 in zip(color1, color2))
