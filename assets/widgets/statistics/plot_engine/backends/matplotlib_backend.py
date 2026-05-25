# backends/matplotlib_backend.py
"""
Matplotlib backend for the PlotEngine.

This module provides a Textual widget that displays a simple "View Plot"
button. When the button is pressed, a Matplotlib figure is built from the
provided ``PlotData`` and shown in an external window using the TkAgg
backend. The heavy lifting of figure construction is delegated to the
private ``_build_figure_for_display`` helper, which mirrors the logic used
by the other backends (e.g., the Sixel and Plotext backends) but forces
the interactive TkAgg backend so the window can be displayed without
blocking the Textual UI thread.

Only comments have been added; the runtime behaviour of the code is
unchanged.
"""

from __future__ import annotations

import threading
import sys
from pathlib import Path
from typing import TYPE_CHECKING

from textual.widget import Widget
from textual.widgets import Button, Static
from textual.containers import Center, Vertical
from textual.app import ComposeResult
from textual.message import Message

# Ensure parent directory is in path
_parent = Path(__file__).parent.parent
if str(_parent) not in sys.path:
    sys.path.insert(0, str(_parent))

if TYPE_CHECKING:
    from plot_callback import PlotData


class MatplotlibPlotWidget(Widget):
    """
    Renders a centered "View Plot" button.
    When clicked, opens the matplotlib figure in an external window.
    """

    DEFAULT_CSS = """
    MatplotlibPlotWidget {
        width: 100%;
        height: 100%;
        align: center middle;
    }

    MatplotlibPlotWidget Center {
        width: 100%;
        height: 100%;
        align: center middle;
    }

    MatplotlibPlotWidget Button {
        min-width: 20;
    }

    MatplotlibPlotWidget .mpl-status {
        text-align: center;
        color: $text-muted;
        margin-top: 1;
    }
    """

    class PlotOpened(Message):
        """Message posted when the external Matplotlib window is opened."""
        pass

    class PlotClosed(Message):
        """Message posted when the external Matplotlib window is closed."""
        pass

    def __init__(
        self,
        plot_data: "PlotData",
        *,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        super().__init__(id=id, classes=classes)
        self._plot_data = plot_data
        self._plot_thread: threading.Thread | None = None

    def compose(self) -> ComposeResult:
        """Compose the UI: a button and a status text."""
        with Center():
            with Vertical():
                yield Center(
                    Button("View Plot", id="mpl-view-btn", variant="primary")
                )
                yield Static(
                    "Click to open plot in external window",
                    classes="mpl-status",
                    id="mpl-status",
                )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press – start the Matplotlib window if the correct button."""
        if event.button.id == "mpl-view-btn":
            self._open_matplotlib_window()

    def _open_matplotlib_window(self) -> None:
        """Open the matplotlib figure in a separate thread so Textual isn't blocked."""
        status = self.query_one("#mpl-status", Static)
        status.update("Opening plot window...")
        self.post_message(self.PlotOpened())

        # Capture references for the thread
        plot_data = self._plot_data
        app = self.app
        widget_self = self

        def _show():
            """Thread target: build the figure, show it, and report back to the UI."""
            try:
                import matplotlib
                # Must set backend BEFORE importing pyplot
                matplotlib.use("TkAgg")
                import matplotlib.pyplot as mpl_plt

                # Build the figure with TkAgg backend
                fig, ax = _build_figure_for_display(plot_data)

                # Show blocking - thread waits until window is closed
                mpl_plt.show(block=True)

                # Clean up
                mpl_plt.close(fig)

                app.call_from_thread(_on_closed)

            except Exception as exc:
                import traceback
                error_msg = f"{exc}"
                app.call_from_thread(_on_error, error_msg)

        def _on_closed():
            """Callback executed on the main thread after the plot window closes."""
            try:
                status = widget_self.query_one("#mpl-status", Static)
                status.update("Plot window closed. Click to reopen.")
                widget_self.post_message(widget_self.PlotClosed())
            except Exception:
                pass

        def _on_error(error_msg: str):
            """Callback executed on the main thread if an exception occurs."""
            try:
                status = widget_self.query_one("#mpl-status", Static)
                status.update(f"[red]Error: {error_msg}[/red]")
            except Exception:
                pass

        self._plot_thread = threading.Thread(target=_show, daemon=True)
        self._plot_thread.start()


def _build_figure_for_display(data):
    """
    Build a matplotlib figure using TkAgg backend for interactive display.

    This function mirrors the logic used by the shared ``build_matplotlib_figure``
    helper but constructs the figure directly with the TkAgg backend, which is
    required for the external window opened by ``MatplotlibPlotWidget``.
    It handles all supported plot types, optional statistical overlays, and
    legend creation based on the contents of the supplied ``PlotData`` instance.
    """
    import numpy as np
    import matplotlib.pyplot as plt
    from plot_callback import PlotType

    fig, ax = plt.subplots(figsize=data._figsize, dpi=data._dpi)

    def _draw_series(ax, x, y, plot_type, color, label):
        """Draw a single data series according to its PlotType."""
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

    # Draw primary data series
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

    # Draw any additional series defined in PlotData
    for s in data.series:
        _draw_series(ax, s["x"], s["y"], s["plot_type"], s["color"], s["label"])

    # Overlays: mean, median, normal distribution, and stats box
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
                    pass
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

    # Axis labels and title
    if data._title:
        ax.set_title(data._title)
    if data._xlabel:
        ax.set_xlabel(data._xlabel)
    if data._ylabel:
        ax.set_ylabel(data._ylabel)

    # Legend handling – only add if there are labeled elements
    handles, labels = ax.get_legend_handles_labels()
    if any(labels):
        ax.legend()

    fig.tight_layout()
    return fig, ax
