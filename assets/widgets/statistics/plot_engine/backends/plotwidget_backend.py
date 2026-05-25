# backends/plotwidget_backend.py
#
# This module provides a Textual widget that wraps the ``PlotWidget`` from the
# ``textual-plot`` library.  The wrapper translates the generic ``PlotData``
# structure used throughout the application into the concrete API calls that
# ``PlotWidget`` expects.  All heavy‑lifting (rendering, interaction) is still
# performed by ``PlotWidget`` – this class merely adapts data, handles the case
# where the optional dependency is missing, and offers a convenient ``refresh``
# method for updating the plot after the underlying data changes.

from __future__ import annotations

import sys
from pathlib import Path
from typing import TYPE_CHECKING

from textual.widget import Widget
from textual.app import ComposeResult
from textual_plot import HiResMode

# Ensure parent directory is in path so that relative imports (e.g. plot_callback)
# resolve correctly when the package is executed as a script.
_parent = Path(__file__).parent.parent
if str(_parent) not in sys.path:
    sys.path.insert(0, str(_parent))

if TYPE_CHECKING:
    # Imported only for type checking; at runtime we import lazily inside methods.
    from plot_callback import PlotData, PlotType

# Attempt to import the optional ``textual-plot`` dependency.
# If it is not installed we fall back to a simple error message widget.
try:
    from textual_plot import PlotWidget
    HAS_PLOTWIDGET = True
except ImportError:
    HAS_PLOTWIDGET = False


class PlotextPlotWidget(Widget):
    """
    Textual widget that embeds a ``PlotWidget`` (from ``textual-plot``) and
    populates it based on a ``PlotData`` instance.

    The widget is responsible for:
    * Detecting whether ``textual-plot`` is available.
    * Rendering a helpful error message when the library is missing.
    * Translating the generic ``PlotData`` fields (x, y, series, plot type,
      overlays, etc.) into concrete ``PlotWidget.plot`` calls.
    * Providing a ``refresh_plot`` method to re‑populate the plot after data
      changes without recreating the widget.
    """

    DEFAULT_CSS = """
    PlotextPlotWidget {
        width: 100%;
        height: 100%;
        min-height: 15;
    }

    PlotextPlotWidget PlotWidget {
        width: 100%;
        height: 100%;
    }

    PlotextPlotWidget .pw-error {
        color: $error;
        text-align: center;
        padding: 2;
    }
    """

    def __init__(
        self,
        plot_data: "PlotData",
        *,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        """
        Initialise the widget with the ``PlotData`` that describes what should be
        plotted.

        Parameters
        ----------
        plot_data: PlotData
            The data container holding series, axis values, plot type, and
            configuration flags (e.g., show mean/median).
        id, classes:
            Standard Textual widget identifiers.
        """
        super().__init__(id=id, classes=classes)
        self._plot_data = plot_data

    def compose(self) -> ComposeResult:
        """
        Build the widget tree.

        If ``textual-plot`` is unavailable we render a static error message.
        Otherwise we instantiate the actual ``PlotWidget`` which will later be
        populated with data in ``on_mount``.
        """
        if not HAS_PLOTWIDGET:
            from textual.widgets import Static
            yield Static(
                "[red]Error: textual-plot is not installed.\n"
                "Install with: pip install textual-plot[/red]",
                classes="pw-error",
            )
        else:
            yield PlotWidget()

    def on_mount(self) -> None:
        """
        Called by Textual after the widget has been added to the DOM.

        If the backend is present we retrieve the ``PlotWidget`` instance and
        populate it with the data from ``self._plot_data``.
        """
        if not HAS_PLOTWIDGET:
            return

        pw = self.query_one(PlotWidget)
        self._populate_plot(pw)

    def _populate_plot(self, pw: "PlotWidget") -> None:
        """
        Translate the generic ``PlotData`` fields into concrete ``PlotWidget``
        calls.

        The method handles several scenarios:
        * Primary series with both x and y values (line, scatter, bar, boxplot).
        * Histograms where only y (or x) is supplied.
        * Fallback to index‑based x values when only one axis is present.
        * Additional user‑defined series stored in ``PlotData.series``.
        * Optional overlay lines for mean and median values.

        Parameters
        ----------
        pw: PlotWidget
            The concrete widget that will render the plot.
        """
        import numpy as np
        from plot_callback import PlotType

        data = self._plot_data

        has_x = bool(data._x)
        has_y = bool(data._y)

        # Primary series handling -------------------------------------------------
        if has_x and has_y:
            # Both axes provided – choose rendering based on plot type.
            if data._plot_type in (PlotType.LINE, PlotType.SCATTER, PlotType.BAR):
                pw.plot(x=data._x, y=data._y, hires_mode=HiResMode.BRAILLE,)
            elif data._plot_type == PlotType.HISTOGRAM:
                # Compute histogram from y values.
                bins = data._bins if data._bins else 10
                counts, bin_edges = np.histogram(data._y, bins=bins)
                centers = [
                    (bin_edges[i] + bin_edges[i + 1]) / 2
                    for i in range(len(counts))
                ]
                pw.plot(x=centers, y=counts.tolist(), hires_mode=HiResMode.BRAILLE,)
            elif data._plot_type == PlotType.BOXPLOT:
                pw.plot(x=data._x, y=data._y, hires_mode=HiResMode.BRAILLE,)

        elif has_y:
            # Only y provided – treat as histogram or simple index plot.
            if data._plot_type == PlotType.HISTOGRAM:
                bins = data._bins if data._bins else 10
                counts, bin_edges = np.histogram(data._y, bins=bins)
                centers = [
                    (bin_edges[i] + bin_edges[i + 1]) / 2
                    for i in range(len(counts))
                ]
                pw.plot(x=centers, y=counts.tolist(), hires_mode=HiResMode.BRAILLE,)
            else:
                pw.plot(x=list(range(len(data._y))), y=data._y, hires_mode=HiResMode.BRAILLE,)

        elif has_x:
            # Only x provided – similar logic to the y‑only case.
            if data._plot_type == PlotType.HISTOGRAM:
                bins = data._bins if data._bins else 10
                counts, bin_edges = np.histogram(data._x, bins=bins)
                centers = [
                    (bin_edges[i] + bin_edges[i + 1]) / 2
                    for i in range(len(counts))
                ]
                pw.plot(x=centers, y=counts.tolist(), hires_mode=HiResMode.BRAILLE,)
            else:
                pw.plot(x=list(range(len(data._x))), y=data._x, hires_mode=HiResMode.BRAILLE)

        # Additional series (user‑defined) ----------------------------------------
        for series in data.series:
            if series["x"] and series["y"]:
                pw.plot(x=series["x"], y=series["y"], hires_mode=HiResMode.BRAILLE)

        # Overlay lines for statistical markers (mean / median) --------------------
        values = data._y if data._y else data._x
        if values and (has_x or has_y):
            # Determine the x‑range over which to draw the overlay.
            if data._plot_type == PlotType.HISTOGRAM:
                bins = data._bins if data._bins else 10
                _, bin_edges = np.histogram(values, bins=bins)
                xmin, xmax = bin_edges[0], bin_edges[-1]
            elif data._x:
                xmin, xmax = min(data._x), max(data._x)
            else:
                xmin, xmax = 0, len(values) - 1

            if data._show_mean:
                mean_val = float(np.mean(values))
                pw.plot(x=[xmin, xmax], y=[mean_val, mean_val], hires_mode=HiResMode.BRAILLE)

            if data._show_median:
                median_val = float(np.median(values))
                pw.plot(x=[xmin, xmax], y=[median_val, median_val], hires_mode=HiResMode.BRAILLE)

    def refresh_plot(self) -> None:
        """
        Re‑populate the underlying ``PlotWidget`` with the current ``PlotData``.
        This method can be called after the data has been mutated to update the
        visualisation without recreating the widget.
        """
        if HAS_PLOTWIDGET:
            pw = self.query_one(PlotWidget)
            self._populate_plot(pw)
