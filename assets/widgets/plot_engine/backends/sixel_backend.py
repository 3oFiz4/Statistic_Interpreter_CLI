# backends/sixel_backend.py

"""
Sixel backend for rendering Matplotlib figures as terminal graphics.

This module defines `SixelPlotWidget`, a Textual widget that converts a
Matplotlib figure into a Pillow (PIL) image and then displays it using the
`SixelImage` widget from the `textual-image` package.  The widget falls back
to an error message when the optional dependencies are not installed.

The implementation is deliberately lightweight:
* It builds the figure using the shared `build_matplotlib_figure` helper.
* The figure is saved to an in‑memory PNG buffer.
* Pillow loads the PNG into an `Image` object.
* `SixelImage` renders the image as a sixel graphic directly in the terminal.

All heavy lifting (Matplotlib rendering) is performed off‑screen using the
Agg backend, so no GUI window is required.
"""

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


# ----------------------------------------------------------------------
# Widget definition
# ----------------------------------------------------------------------
class SixelPlotWidget(Widget):
    """
    Renders the matplotlib figure as an image using textual-image SixelImage.
    """

    # ------------------------------------------------------------------
    # Styling
    # ------------------------------------------------------------------
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

    # ------------------------------------------------------------------
    # Initialization
    # ------------------------------------------------------------------
    def __init__(
        self,
        plot_data: "PlotData",
        temp_dir: Path | None = None,
        *,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        """
        Create a new SixelPlotWidget.

        Parameters
        ----------
        plot_data: PlotData
            The data and configuration required to build the Matplotlib figure.
        temp_dir: Path | None
            Unused placeholder kept for API compatibility with other backends.
        id, classes:
            Standard Textual widget identifiers.
        """
        super().__init__(id=id, classes=classes)
        self._plot_data = plot_data
        self._pil_image: "PILImage.Image | None" = None

    # ------------------------------------------------------------------
    # UI composition
    # ------------------------------------------------------------------
    def compose(self) -> ComposeResult:
        """
        Build the widget's initial UI.

        If the optional `textual-image` package is missing, an error message
        is shown. Otherwise a container with a loading placeholder is created;
        the actual image will be mounted later once rendering completes.
        """
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

    # ------------------------------------------------------------------
    # Lifecycle hook – mount
    # ------------------------------------------------------------------
    def on_mount(self) -> None:
        """
        Called by Textual when the widget is added to the DOM.

        Triggers the image rendering process if the required dependencies are
        available.
        """
        if HAS_TEXTUAL_IMAGE:
            self._render_image()

    # ------------------------------------------------------------------
    # Rendering helper
    # ------------------------------------------------------------------
    def _render_image(self) -> None:
        """
        Generate the Matplotlib figure, convert it to a Pillow image, and
        replace the loading placeholder with a `SixelImage` widget.

        Errors during rendering are caught and displayed in the UI.
        """
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
            # Show a friendly error message if something goes wrong
            try:
                loading = self.query_one("#loading-msg", Static)
                loading.update(f"[red]Image render error: {exc}[/red]")
                loading.add_class("image-error")
                loading.remove_class("image-loading")
            except Exception:
                pass

    # ------------------------------------------------------------------
    # Figure → Pillow conversion
    # ------------------------------------------------------------------
    def _create_pil_image(self) -> "PILImage.Image":
        """
        Build a Matplotlib figure using the shared helper and return it as a
        Pillow `Image` object.

        The function:
        1. Switches Matplotlib to the non‑interactive Agg backend.
        2. Calls `build_matplotlib_figure` to obtain a Figure/Axes pair.
        3. Saves the figure to an in‑memory PNG buffer.
        4. Loads the PNG data into a Pillow image and returns a copy.
        """
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

    # ------------------------------------------------------------------
    # Public API – refresh
    # ------------------------------------------------------------------
    def refresh_plot(self) -> None:
        """
        Re‑render the plot after the underlying data has changed.

        The method clears any existing image widget, shows the loading
        placeholder again, and then calls `_render_image` to generate a fresh
        image.
        """
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

    # ------------------------------------------------------------------
    # Cleanup
    # ------------------------------------------------------------------
    def cleanup(self) -> None:
        """
        Release the Pillow image resource when the widget is no longer needed.

        This helps avoid holding onto large image buffers in memory.
        """
        if self._pil_image:
            self._pil_image.close()
            self._pil_image = None
