# plot_callback.py

"""
Provides a high‑level, backend‑agnostic API for creating plots within a
Textual application.  The :class:`PlotCallback` class stores plot data and
configuration, then produces the appropriate Textual widget based on the
selected fallback backend (Matplotlib, Sixel, or Plotext).  The design follows
a fluent interface so calls can be chained:

    plt = PlotCallback(fallback=PlotFallback.PLOTWIDGET)
    plt.x([1, 2, 3]).y([4, 5, 6]).title("Demo").plot_type(PlotType.LINE)

The resulting widget can be yielded in a Textual ``compose`` method.
"""

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
    """Enumeration of available plotting backends.

    - ``MATPLOTLIB``: Uses a Matplotlib figure displayed in an external window.
    - ``SIXEL``: Renders the figure as a sixel image directly in the terminal.
    - ``PLOTWIDGET``: Uses the Plotext backend via ``textual-plot``.
    """
    MATPLOTLIB = "matplotlib"
    SIXEL = "sixel"
    PLOTWIDGET = "plotwidget"  # a.k.a. Plotext via textual-plot


class PlotType(str, Enum):
    """Supported plot types for the primary data series.

    The enum values map directly to the terminology used by the underlying
    backends (e.g., ``line`` for a simple line plot, ``histogram`` for a
    frequency distribution, etc.).
    """
    LINE = "line"
    SCATTER = "scatter"
    BAR = "bar"
    HISTOGRAM = "histogram"
    BOXPLOT = "boxplot"


class PlotData:
    """
    Container for all data and configuration required to render a plot.

    The class is deliberately lightweight – it only stores values; all
    validation and rendering logic lives in the backend widgets.  Attributes
    are prefixed with an underscore to signal that they are internal and
    should be accessed via the public ``PlotCallback`` API.
    """

    def __init__(self) -> None:
        # Primary series data
        self._x: list[float] = []
        self._y: list[float] = []
        # Plot appearance
        self._plot_type: PlotType = PlotType.LINE
        self._title: str = ""
        self._xlabel: str = ""
        self._ylabel: str = ""
        self._color: str = "blue"
        # Arbitrary extra data for backend‑specific extensions
        self._extra_data: dict[str, Any] = {}
        # Support for multiple series (e.g., overlayed lines)
        self._series: list[dict[str, Any]] = []
        # Histogram‑specific options
        self._bins: int | None = None
        # Overlay toggles
        self._show_mean: bool = False
        self._show_median: bool = False
        self._show_stats: bool = False
        self._show_normal: bool = False
        # Figure size and resolution (used by Matplotlib/Sixel)
        self._figsize: tuple[int, int] = (8, 6)
        self._dpi: int = 100

    @property
    def x(self) -> list[float]:
        """X‑axis data for the primary series."""
        return self._x

    @property
    def y(self) -> list[float]:
        """Y‑axis data for the primary series."""
        return self._y

    @property
    def has_data(self) -> bool:
        """True if either the primary series or any additional series contain data."""
        return len(self._x) > 0 or len(self._series) > 0

    @property
    def series(self) -> list[dict[str, Any]]:
        """List of additional series dictionaries."""
        return self._series


class PlotCallback:
    """
    High‑level interface for configuring a plot and obtaining a Textual widget.

    The class stores a :class:`PlotData` instance and provides a fluent API
    (each method returns ``self``) so configuration can be chained.  After
    configuration, call :meth:`widget` to retrieve the backend‑specific widget
    that can be added to a Textual layout.

    Attributes
    ----------
    _fallback : PlotFallback
        Determines which backend widget will be instantiated.
    _data : PlotData
        Holds all plot configuration and series data.
    _widget_id / _widget_classes : optional identifiers for the created widget.
    _temp_dir : Path
        Temporary directory used by the SIXEL backend for image files.
    """

    def __init__(
        self,
        fallback: PlotFallback | str = PlotFallback.PLOTWIDGET,
        *,
        widget_id: str | None = None,
        widget_classes: str | None = None,
    ) -> None:
        # Allow passing a raw string (e.g., from a config file)
        if isinstance(fallback, str):
            fallback = PlotFallback(fallback.lower())
        self._fallback: PlotFallback = fallback
        self._data: PlotData = PlotData()
        self._widget_id: str | None = widget_id
        self._widget_classes: str | None = widget_classes
        # Create a temporary directory for SIXEL image files; cleaned up on delete
        self._temp_dir: Path = Path(tempfile.mkdtemp(prefix="textual_plot_"))

    # ── Fluent API for configuration ────────────────────────────────

    def axis(self, which: str, values: list[float]) -> "PlotCallback":
        """Set axis data. ``which`` must be ``'x'`` or ``'y'``."""
        which = which.lower().strip()
        if which == "x":
            self._data._x = list(values)
        elif which == "y":
            self._data._y = list(values)
        else:
            raise ValueError(f"Unknown axis '{which}'. Use 'x' or 'y'.")
        return self

    def x(self, values: list[float]) -> "PlotCallback":
        """Shortcut to set the X‑axis data."""
        self._data._x = list(values)
        return self

    def y(self, values: list[float]) -> "PlotCallback":
        """Shortcut to set the Y‑axis data."""
        self._data._y = list(values)
        return self

    def title(self, t: str) -> "PlotCallback":
        """Set the plot title."""
        self._data._title = t
        return self

    def xlabel(self, label: str) -> "PlotCallback":
        """Set the X‑axis label."""
        self._data._xlabel = label
        return self

    def ylabel(self, label: str) -> "PlotCallback":
        """Set the Y‑axis label."""
        self._data._ylabel = label
        return self

    def color(self, c: str) -> "PlotCallback":
        """Set the default line/marker color."""
        self._data._color = c
        return self

    def plot_type(self, pt: PlotType | str) -> "PlotCallback":
        """Select the primary plot type (line, scatter, etc.)."""
        if isinstance(pt, str):
            pt = PlotType(pt.lower())
        self._data._plot_type = pt
        return self

    def bins(self, n: int) -> "PlotCallback":
        """Set bin count for histogram plots."""
        self._data._bins = n
        return self

    def figsize(self, w: int, h: int) -> "PlotCallback":
        """Set figure width and height (in inches) for Matplotlib/Sixel."""
        self._data._figsize = (w, h)
        return self

    def dpi(self, d: int) -> "PlotCallback":
        """Set figure resolution (dots per inch)."""
        self._data._dpi = d
        return self

    def show_mean(self, val: bool = True) -> "PlotCallback":
        """Toggle display of a mean overlay."""
        self._data._show_mean = val
        return self

    def show_median(self, val: bool = True) -> "PlotCallback":
        """Toggle display of a median overlay."""
        self._data._show_median = val
        return self

    def show_stats(self, val: bool = True) -> "PlotCallback":
        """Toggle display of basic statistics (mean, median, etc.)."""
        self._data._show_stats = val
        return self

    def show_normal(self, val: bool = True) -> "PlotCallback":
        """Toggle overlay of a normal distribution curve."""
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
        """
        Add an additional data series for multi‑line or overlay plots.

        Parameters
        ----------
        x, y : list[float]
            Data points for the series.
        label : str, optional
            Legend label for the series.
        color : str, optional
            Override the default color for this series.
        plot_type : PlotType | str, optional
            Plot type for this series (defaults to line).
        """
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
        """Store arbitrary extra data for backend‑specific extensions."""
        self._data._extra_data[key] = value
        return self

    # ── Fallback management ─────────────────────────────────────────

    @property
    def fallback(self) -> PlotFallback:
        """Current backend fallback."""
        return self._fallback

    @fallback.setter
    def fallback(self, value: PlotFallback | str) -> None:
        """Set a new backend fallback, accepting either enum or string."""
        if isinstance(value, str):
            value = PlotFallback(value.lower())
        self._fallback = value

    def set_fallback(self, value: PlotFallback | str) -> "PlotCallback":
        """Fluent setter for the fallback backend."""
        self.fallback = value
        return self

    # ── Widget factory ──────────────────────────────────────────────

    def widget(self) -> Widget:
        """
        Instantiate and return the appropriate Textual widget based on the
        selected fallback backend.

        Returns
        -------
        Widget
            One of ``MatplotlibPlotWidget``, ``SixelPlotWidget`` or
            ``PlotextPlotWidget`` configured with the stored ``PlotData``.
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
        """Remove temporary files created for SIXEL rendering."""
        if self._temp_dir.exists():
            shutil.rmtree(self._temp_dir, ignore_errors=True)

    def __del__(self) -> None:
        """Ensure temporary resources are cleaned up when the object is garbage‑collected."""
        self.cleanup()
