# backends/plotwidget_backend.py

from __future__ import annotations

import sys
from pathlib import Path
from typing import TYPE_CHECKING

from textual.widget import Widget
from textual.app import ComposeResult
from textual_plot import HiResMode

# Ensure parent directory is in path
_parent = Path(__file__).parent.parent
if str(_parent) not in sys.path:
    sys.path.insert(0, str(_parent))

if TYPE_CHECKING:
    from plot_callback import PlotData, PlotType

try:
    from textual_plot import PlotWidget
    HAS_PLOTWIDGET = True
except ImportError:
    HAS_PLOTWIDGET = False


class PlotextPlotWidget(Widget):
    """
    Wraps the textual-plot PlotWidget.
    Translates PlotData into PlotWidget API calls.
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
        super().__init__(id=id, classes=classes)
        self._plot_data = plot_data

    def compose(self) -> ComposeResult:
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
        if not HAS_PLOTWIDGET:
            return

        pw = self.query_one(PlotWidget)
        self._populate_plot(pw)

    def _populate_plot(self, pw: "PlotWidget") -> None:
        """Translate PlotData into PlotWidget API calls."""
        import numpy as np
        from plot_callback import PlotType

        data = self._plot_data

        has_x = bool(data._x)
        has_y = bool(data._y)

        # Primary series
        if has_x and has_y:
            # Both provided - line, scatter, bar
            if data._plot_type in (PlotType.LINE, PlotType.SCATTER, PlotType.BAR):
                pw.plot(x=data._x, y=data._y, hires_mode=HiResMode.BRAILLE,)
            elif data._plot_type == PlotType.HISTOGRAM:
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
            # Only y provided - typically histogram
            if data._plot_type == PlotType.HISTOGRAM:
                bins = data._bins if data._bins else 10
                counts, bin_edges = np.histogram(data._y, bins=bins)
                centers = [
                    (bin_edges[i] + bin_edges[i + 1]) / 2
                    for i in range(len(counts))
                ]
                pw.plot(x=centers, y=counts.tolist(), hires_mode=HiResMode.BRAILLE,)
            else:
                # Default: use indices as x
                pw.plot(x=list(range(len(data._y))), y=data._y, hires_mode=HiResMode.BRAILLE,)

        elif has_x:
            # Only x provided - histogram or use as y with indices
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

        # Additional series
        for series in data.series:
            if series["x"] and series["y"]:
                pw.plot(x=series["x"], y=series["y"], hires_mode=HiResMode.BRAILLE)

        # Overlays (mean/median lines)
        values = data._y if data._y else data._x
        if values and (has_x or has_y):
            # Determine x range for overlay lines
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
        if HAS_PLOTWIDGET:
            pw = self.query_one(PlotWidget)
            self._populate_plot(pw)
