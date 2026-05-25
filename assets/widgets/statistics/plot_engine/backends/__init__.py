# backends/__init__.py

"""Shared matplotlib figure-building logic used by both Matplotlib and Sixel backends."""

from __future__ import annotations

import numpy as np

# Use direct import (not relative) since plot_callback.py is at project root
import sys
from pathlib import Path

# Ensure parent directory is in path for imports
_parent = Path(__file__).parent.parent
if str(_parent) not in sys.path:
    sys.path.insert(0, str(_parent))

from plot_callback import PlotType


def build_matplotlib_figure(data):
    """
    Construct and return a matplotlib Figure + Axes from the given PlotData.
    This is shared between the Matplotlib (popup window) backend and the
    Sixel (export-to-image) backend.
    """
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.figure import Figure

    fig: Figure
    ax: plt.Axes
    fig, ax = plt.subplots(figsize=data._figsize, dpi=data._dpi)

    def _draw_series(ax, x, y, plot_type, color, label):
        """Draw a single series. Handles cases where x or y might be empty."""
        if plot_type == PlotType.LINE:
            if x and y:
                ax.plot(x, y, color=color or None, label=label or None)
        elif plot_type == PlotType.SCATTER:
            if x and y:
                ax.scatter(x, y, color=color or None, label=label or None)
        elif plot_type == PlotType.BAR:
            if x and y:
                ax.bar(x, y, color=color or None, label=label or None)
        elif plot_type == PlotType.HISTOGRAM:
            # Histogram only needs one data array
            hist_data = y if y else x
            if hist_data:
                bins = data._bins if data._bins else "auto"
                ax.hist(
                    hist_data,
                    bins=bins,
                    color=color or None,
                    label=label or None,
                    density=False,
                    alpha=0.7,
                    edgecolor="black",
                )
        elif plot_type == PlotType.BOXPLOT:
            box_data = y if y else x
            if box_data:
                ax.boxplot(box_data, vert=True)

    # Draw primary data - handle cases where only x or only y is provided
    has_x = bool(data._x)
    has_y = bool(data._y)

    if has_x or has_y:
        _draw_series(
            ax,
            data._x if has_x else [],
            data._y if has_y else [],
            data._plot_type,
            data._color,
            "",
        )

    # Draw additional series
    for s in data.series:
        _draw_series(
            ax,
            s["x"],
            s["y"],
            s["plot_type"],
            s["color"],
            s["label"],
        )

    # Overlays (mean, median, etc.) - use whichever data array exists
    values = data._y if data._y else data._x
    if values:
        if data._show_mean:
            mean_val = float(np.mean(values))
            ax.axvline(
                mean_val,
                color="red",
                linestyle="--",
                linewidth=1.5,
                label=f"Mean: {mean_val:.2f}",
            )

        if data._show_median:
            median_val = float(np.median(values))
            ax.axvline(
                median_val,
                color="green",
                linestyle="-.",
                linewidth=1.5,
                label=f"Median: {median_val:.2f}",
            )

        if data._show_normal and data._plot_type == PlotType.HISTOGRAM:
            mean_val = float(np.mean(values))
            std_val = float(np.std(values))
            if std_val > 0:
                xmin, xmax = ax.get_xlim()
                x_range = np.linspace(xmin, xmax, 200)
                try:
                    from scipy.stats import norm
                    pdf = norm.pdf(x_range, mean_val, std_val)
                    bin_count = data._bins if data._bins else 10
                    n = len(values)
                    bin_width = (max(values) - min(values)) / bin_count
                    ax.plot(
                        x_range,
                        pdf * n * bin_width,
                        color="orange",
                        linewidth=2,
                        label="Normal Distribution",
                    )
                except ImportError:
                    pass  # scipy not installed

        if data._show_stats:
            stats_text = (
                f"n = {len(values)}\n"
                f"μ = {np.mean(values):.2f}\n"
                f"σ = {np.std(values):.2f}\n"
                f"min = {np.min(values):.2f}\n"
                f"max = {np.max(values):.2f}"
            )
            ax.text(
                0.98,
                0.98,
                stats_text,
                transform=ax.transAxes,
                fontsize=9,
                verticalalignment="top",
                horizontalalignment="right",
                bbox=dict(boxstyle="round,pad=0.3", facecolor="wheat", alpha=0.8),
            )

    if data._title:
        ax.set_title(data._title)
    if data._xlabel:
        ax.set_xlabel(data._xlabel)
    if data._ylabel:
        ax.set_ylabel(data._ylabel)

    # Show legend if any labels exist
    handles, labels = ax.get_legend_handles_labels()
    if any(labels):
        ax.legend()

    fig.tight_layout()
    return fig, ax
