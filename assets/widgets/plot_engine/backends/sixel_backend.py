# backends/sixel_backend.py

from __future__ import annotations

import io
import sys
from pathlib import Path
from typing import TYPE_CHECKING

from textual.widget import Widget
from textual.widgets import Static
from textual.app import ComposeResult
from textual.containers import Container

# Ensure parent directory is in path
_parent = Path(__file__).parent.parent
if str(_parent) not in sys.path:
    sys.path.insert(0, str(_parent))

# Try to import textual-image SixelImage and PIL
try:
    from textual_image.widget import SixelImage
    from PIL import Image as PILImage
    HAS_TEXTUAL_IMAGE = True
except ImportError:
    HAS_TEXTUAL_IMAGE = False

if TYPE_CHECKING:
    from plot_callback import PlotData


class SixelPlotWidget(Widget):
    """
    Renders the matplotlib figure as an image using textual-image SixelImage.
    """

    DEFAULT_CSS = """
    SixelPlotWidget {
        width: 100%;
        height: 100%;
        min-height: 20;
    }

    SixelPlotWidget #image-container {
        width: 100%;
        height: 100%;
    }

    SixelPlotWidget SixelImage {
        width: 100%;
        height: 100%;
    }

    SixelPlotWidget .image-error {
        color: $error;
        text-align: center;
        padding: 1;
    }

    SixelPlotWidget .image-loading {
        text-align: center;
        color: $text-muted;
    }
    """

    def __init__(
        self,
        plot_data: "PlotData",
        temp_dir: Path | None = None,
        *,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        super().__init__(id=id, classes=classes)
        self._plot_data = plot_data
        self._pil_image: "PILImage.Image | None" = None

    def compose(self) -> ComposeResult:
        if not HAS_TEXTUAL_IMAGE:
            yield Static(
                "[red]Error: textual-image is not installed.\n"
                "Install with: pip install textual-image[/red]",
                classes="image-error",
            )
        else:
            yield Container(
                Static("Rendering plot...", classes="image-loading", id="loading-msg"),
                id="image-container",
            )

    def on_mount(self) -> None:
        if HAS_TEXTUAL_IMAGE:
            self._render_image()

    def _render_image(self) -> None:
        container = self.query_one("#image-container", Container)

        try:
            # Generate PIL Image from matplotlib
            self._pil_image = self._create_pil_image()

            # Remove loading message
            try:
                loading = self.query_one("#loading-msg", Static)
                loading.remove()
            except Exception:
                pass

            # Create SixelImage widget directly
            image_widget = SixelImage(self._pil_image)
            container.mount(image_widget)

        except Exception as exc:
            try:
                loading = self.query_one("#loading-msg", Static)
                loading.update(f"[red]Image render error: {exc}[/red]")
                loading.add_class("image-error")
                loading.remove_class("image-loading")
            except Exception:
                pass

    def _create_pil_image(self) -> "PILImage.Image":
        """Create a PIL Image from the matplotlib figure (in memory)."""
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        from backends import build_matplotlib_figure

        fig, ax = build_matplotlib_figure(self._plot_data)

        # Save figure to bytes buffer
        buf = io.BytesIO()
        fig.savefig(buf, format="png", bbox_inches="tight", dpi=100)
        plt.close(fig)

        # Convert to PIL Image
        buf.seek(0)
        pil_image = PILImage.open(buf).copy()
        buf.close()

        return pil_image

    def refresh_plot(self) -> None:
        """Re-render the plot after data changes."""
        if not HAS_TEXTUAL_IMAGE:
            return

        container = self.query_one("#image-container", Container)

        # Remove existing children
        for child in list(container.children):
            child.remove()

        # Add loading message
        container.mount(
            Static("Rendering plot...", classes="image-loading", id="loading-msg")
        )

        # Re-render
        self._render_image()

    def cleanup(self) -> None:
        """Clean up PIL image reference."""
        if self._pil_image:
            self._pil_image.close()
            self._pil_image = None
