# backends/matplotlib_backend.py
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
        pass

    class PlotClosed(Message):
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
            try:
                status = widget_self.query_one("#mpl-status", Static)
                status.update("Plot window closed. Click to reopen.")
                widget_self.post_message(widget_self.PlotClosed())
            except Exception:
                pass

        def _on_error(error_msg: str):
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
    Duplicates the logic from build_matplotlib_figure but for TkAgg.
    """
    import numpy as np
    import matplotlib.pyplot as plt
    from plot_callback import PlotType

    fig, ax = plt.subplots(figsize=data._figsize, dpi=data._dpi)

    def _draw_series(ax, x, y, plot_type, color, label):
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

    # Draw primary data
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
        _draw_series(ax, s["x"], s["y"], s["plot_type"], s["color"], s["label"])

    # Overlays
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

    if data._title:
        ax.set_title(data._title)
    if data._xlabel:
        ax.set_xlabel(data._xlabel)
    if data._ylabel:
        ax.set_ylabel(data._ylabel)

    handles, labels = ax.get_legend_handles_labels()
    if any(labels):
        ax.legend()

    fig.tight_layout()
    return fig, ax
