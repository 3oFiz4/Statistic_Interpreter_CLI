# plot_callback.py

from __future__ import annotations

import os
import tempfile
import subprocess
import shutil
from enum import Enum
from typing import Optional, Any
from pathlib import Path

from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Button, Static
from textual.containers import Container, Vertical, Center
from textual.message import Message
from textual.reactive import reactive


class PlotFallback(str, Enum):
    """Enumeration of available plotting backends."""
    MATPLOTLIB = "matplotlib"
    SIXEL = "sixel"
    PLOTWIDGET = "plotwidget"  # a.k.a. Plotext via textual-plot


class PlotType(str, Enum):
    """Supported plot types."""
    LINE = "line"
    SCATTER = "scatter"
    BAR = "bar"
    HISTOGRAM = "histogram"
    BOXPLOT = "boxplot"


class PlotData:
    """
    Holds the data and configuration for a single plot.
    This is backend-agnostic; backends consume this to render.
    """

    def __init__(self) -> None:
        self._x: list[float] = []
        self._y: list[float] = []
        self._plot_type: PlotType = PlotType.LINE
        self._title: str = ""
        self._xlabel: str = ""
        self._ylabel: str = ""
        self._color: str = "blue"
        self._extra_data: dict[str, Any] = {}
        self._series: list[dict[str, Any]] = []  # multiple series support
        self._bins: int | None = None
        self._show_mean: bool = False
        self._show_median: bool = False
        self._show_stats: bool = False
        self._show_normal: bool = False
        self._figsize: tuple[int, int] = (8, 6)
        self._dpi: int = 100

    @property
    def x(self) -> list[float]:
        return self._x

    @property
    def y(self) -> list[float]:
        return self._y

    @property
    def has_data(self) -> bool:
        return len(self._x) > 0 or len(self._series) > 0

    @property
    def series(self) -> list[dict[str, Any]]:
        return self._series


class PlotCallback:
    """
    The main plotting interface. Users create an instance, configure axes,
    plot type, overlays, etc. Then mount it inside Textual as a widget
    via `.widget()`, which returns the appropriate widget for the chosen backend.

    Attributes:
        _fallback: Determines which backend to use for rendering.

    Usage:
        plt = PlotCallback(fallback=PlotFallback.PLOTWIDGET)
        plt.axis("x", [1, 2, 3, 4, 5])
        plt.axis("y", [1, 4, 9, 16, 25])
        plt.title("My Plot")
        plt.xlabel("X values")
        plt.ylabel("Y values")
        plt.plot_type(PlotType.LINE)

        # Then in compose():
        yield plt.widget()
    """

    def __init__(
        self,
        fallback: PlotFallback | str = PlotFallback.PLOTWIDGET,
        *,
        widget_id: str | None = None,
        widget_classes: str | None = None,
    ) -> None:
        if isinstance(fallback, str):
            fallback = PlotFallback(fallback.lower())
        self._fallback: PlotFallback = fallback
        self._data: PlotData = PlotData()
        self._widget_id: str | None = widget_id
        self._widget_classes: str | None = widget_classes
        self._temp_dir: Path = Path(tempfile.mkdtemp(prefix="textual_plot_"))

    # ── Fluent API for configuration ────────────────────────────────

    def axis(self, which: str, values: list[float]) -> "PlotCallback":
        """Set axis data. `which` is 'x' or 'y'."""
        which = which.lower().strip()
        if which == "x":
            self._data._x = list(values)
        elif which == "y":
            self._data._y = list(values)
        else:
            raise ValueError(f"Unknown axis '{which}'. Use 'x' or 'y'.")
        return self

    def x(self, values: list[float]) -> "PlotCallback":
        """Shortcut: set x-axis data."""
        self._data._x = list(values)
        return self

    def y(self, values: list[float]) -> "PlotCallback":
        """Shortcut: set y-axis data."""
        self._data._y = list(values)
        return self

    def title(self, t: str) -> "PlotCallback":
        self._data._title = t
        return self

    def xlabel(self, label: str) -> "PlotCallback":
        self._data._xlabel = label
        return self

    def ylabel(self, label: str) -> "PlotCallback":
        self._data._ylabel = label
        return self

    def color(self, c: str) -> "PlotCallback":
        self._data._color = c
        return self

    def plot_type(self, pt: PlotType | str) -> "PlotCallback":
        if isinstance(pt, str):
            pt = PlotType(pt.lower())
        self._data._plot_type = pt
        return self

    def bins(self, n: int) -> "PlotCallback":
        """Set bin count for histograms."""
        self._data._bins = n
        return self

    def figsize(self, w: int, h: int) -> "PlotCallback":
        self._data._figsize = (w, h)
        return self

    def dpi(self, d: int) -> "PlotCallback":
        self._data._dpi = d
        return self

    def show_mean(self, val: bool = True) -> "PlotCallback":
        self._data._show_mean = val
        return self

    def show_median(self, val: bool = True) -> "PlotCallback":
        self._data._show_median = val
        return self

    def show_stats(self, val: bool = True) -> "PlotCallback":
        self._data._show_stats = val
        return self

    def show_normal(self, val: bool = True) -> "PlotCallback":
        self._data._show_normal = val
        return self

    def add_series(
        self,
        x: list[float],
        y: list[float],
        *,
        label: str = "",
        color: str = "",
        plot_type: PlotType | str = PlotType.LINE,
    ) -> "PlotCallback":
        """Add an additional data series for multi-line / overlay plots."""
        if isinstance(plot_type, str):
            plot_type = PlotType(plot_type.lower())
        self._data._series.append({
            "x": list(x),
            "y": list(y),
            "label": label,
            "color": color,
            "plot_type": plot_type,
        })
        return self

    def extra(self, key: str, value: Any) -> "PlotCallback":
        """Store arbitrary extra data for custom backend handling."""
        self._data._extra_data[key] = value
        return self

    # ── Fallback management ─────────────────────────────────────────

    @property
    def fallback(self) -> PlotFallback:
        return self._fallback

    @fallback.setter
    def fallback(self, value: PlotFallback | str) -> None:
        if isinstance(value, str):
            value = PlotFallback(value.lower())
        self._fallback = value

    def set_fallback(self, value: PlotFallback | str) -> "PlotCallback":
        """Fluent setter for _fallback."""
        self.fallback = value
        return self

    # ── Widget factory ──────────────────────────────────────────────

        # Inside PlotCallback class, update the widget() method:
    def widget(self) -> Widget:
        """
        Return the appropriate Textual Widget based on `_fallback`.
        """
        if self._fallback == PlotFallback.MATPLOTLIB:
            from .backends.matplotlib_backend import MatplotlibPlotWidget
            return MatplotlibPlotWidget(
                plot_data=self._data,
                id=self._widget_id,
                classes=self._widget_classes,
            )

        elif self._fallback == PlotFallback.SIXEL:
            from .backends.sixel_backend import SixelPlotWidget
            return SixelPlotWidget(
                plot_data=self._data,
                temp_dir=self._temp_dir,
                id=self._widget_id,
                classes=self._widget_classes,
            )

        elif self._fallback == PlotFallback.PLOTWIDGET:
            from .backends.plotwidget_backend import PlotextPlotWidget
            return PlotextPlotWidget(
                plot_data=self._data,
                id=self._widget_id,
                classes=self._widget_classes,
            )

        else:
            raise ValueError(f"Unknown fallback: {self._fallback}")

    # ── Cleanup ─────────────────────────────────────────────────────

    def cleanup(self) -> None:
        """Remove temporary files created for sixel rendering."""
        if self._temp_dir.exists():
            shutil.rmtree(self._temp_dir, ignore_errors=True)

    def __del__(self) -> None:
        self.cleanup()
