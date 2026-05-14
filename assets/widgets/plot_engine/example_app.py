# example_app.py

"""
Example applications demonstrating the PlotCallback system with multiple backends.
Provides three demo apps:
- HistogramApp: interactive histogram with sidebar controls.
- SimpleLineApp: minimal line plot example.
- MultiBackendDemoApp: switch between PlotWidget, Sixel, and Matplotlib backends.
"""

from __future__ import annotations

from textual.app import App, ComposeResult
from textual.widgets import (
    Header,
    Footer,
    Static,
    Button,
    Input,
    Select,
    RadioButton,
    RadioSet,
    Label,
)
from textual.containers import (
    Container,
    Horizontal,
    Vertical,
    Center,
)
from textual.widget import Widget

from plot_callback import PlotCallback, PlotFallback, PlotType
from widgets.plot_container import PlotContainer

# ─── Sample Data ────────────────────────────────────────────────────

SAMPLE_X = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
SAMPLE_Y = [1, 4, 9, 16, 25, 36, 49, 64, 81, 100]

HISTOGRAM_DATA = [
    2.1, 3.5, 3.8, 4.0, 4.2, 4.5, 4.7, 5.0, 5.1, 5.3,
    5.5, 5.7, 5.9, 6.0, 6.1, 6.3, 6.5, 6.8, 7.0, 7.2,
    7.5, 7.8, 8.0, 8.5, 9.0, 3.2, 4.8, 5.4, 6.2, 6.7,
    5.0, 5.5, 6.0, 6.5, 7.0, 4.5, 5.5, 6.5, 7.5, 8.0,
]


class HistogramApp(App[None]):
    """
    Demo application showing the PlotCallback system embedded in a
    sidebar + main content layout with accordion‑style controls.
    Users can adjust histogram parameters (bins, overlays, backend) and
    see the plot update live.
    """

    CSS = """
    Screen {
        layout: vertical;
    }

    #main-horizontal {
        width: 100%;
        height: 1fr;
    }

    #sidebar {
        width: 35;
        min-width: 30;
        max-width: 40;
        height: 100%;
        border-right: tall $surface-lighten-2;
        padding: 1;
    }

    #sidebar .title {
        text-align: center;
        text-style: bold;
        padding: 1;
        background: $primary;
        color: $text;
        margin-bottom: 1;
    }

    .control-group {
        margin-bottom: 1;
        padding: 0 1;
    }

    .control-label {
        text-style: bold;
        margin-bottom: 0;
    }

    #main-content {
        width: 1fr;
        height: 100%;
        padding: 1;
    }

    #main-content .content-title {
        text-align: center;
        text-style: bold;
        padding: 1;
        margin-bottom: 1;
    }

    #plot-area {
        width: 100%;
        height: 1fr;
        border: round $primary;
    }

    .radio-group-box {
        height: auto;
        margin: 1 0;
        padding: 1;
        border: tall $surface-lighten-1;
    }

    #apply-btn {
        margin-top: 1;
        width: 100%;
    }
    """

    def __init__(self) -> None:
        """
        Initialize the PlotCallback with default histogram settings.
        This object is reused and reconfigured when the user presses "Apply Settings".
        """
        super().__init__()
        # Initialize the PlotCallback with default settings
        self._plt = (
            PlotCallback(fallback=PlotFallback.PLOTWIDGET, widget_id="the-plot")
            .plot_type(PlotType.HISTOGRAM)
            .y(HISTOGRAM_DATA)
            .title("Sample Histogram")
            .xlabel("Value")
            .ylabel("Frequency")
            .bins(10)
            .show_mean(True)
            .color("steelblue")
        )

    def compose(self) -> ComposeResult:
        """Build the UI layout: header, sidebar controls, and main plot area."""
        yield Header(show_clock=True)

        with Horizontal(id="main-horizontal"):
            # ── Sidebar ──────────────────────────────────────────
            with Container(id="sidebar"):
                yield Static("Histogram Controls", classes="title")

                with Vertical():
                    # Y-Axis mode
                    with Vertical(classes="control-group"):
                        yield Label("Y-Axis", classes="control-label")
                        with RadioSet(id="y-axis-radio"):
                            yield RadioButton("Frequency", value=True)
                            yield RadioButton("Probabilistic")

                    # Show overlays
                    with Vertical(classes="control-group"):
                        yield Label("Show Overlays", classes="control-label")
                        with Vertical(classes="radio-group-box"):
                            yield RadioButton("Mean", id="chk-mean", value=True)
                            yield RadioButton("Median", id="chk-median")
                            yield RadioButton("Statistics", id="chk-stats")
                            yield RadioButton("Normal Dist.", id="chk-normal")

                    # Bin size
                    with Vertical(classes="control-group"):
                        yield Label("Bin Size", classes="control-label")
                        yield Input(
                            placeholder="e.g. 10",
                            value="10",
                            id="bin-size-input",
                        )

                    # Fallback selector
                    with Vertical(classes="control-group"):
                        yield Label("Render Backend", classes="control-label")
                        with RadioSet(id="fallback-radio"):
                            yield RadioButton("PlotWidget", value=True, id="rb-plotwidget")
                            yield RadioButton("Sixel (Chafa)", id="rb-sixel")
                            yield RadioButton("Matplotlib", id="rb-matplotlib")

                    # Apply button
                    yield Button(
                        "Apply Settings",
                        id="apply-btn",
                        variant="success",
                    )

            # ── Main Content ─────────────────────────────────────
            with Container(id="main-content"):
                yield Static("Histogram Viewer", classes="content-title")

                with Container(id="plot-area"):
                    yield PlotContainer(
                        self._plt,
                        id="plot-container",
                    )

        yield Footer()

    # ── Event Handlers ──────────────────────────────────────────────

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle clicks on the Apply Settings button."""
        if event.button.id == "apply-btn":
            self._apply_settings()

    def _apply_settings(self) -> None:
        """
        Read all sidebar controls, update the PlotCallback configuration,
        and trigger a rebuild of the PlotContainer.
        """
        # Read bin size
        bin_input = self.query_one("#bin-size-input", Input)
        try:
            bins = int(bin_input.value)
        except (ValueError, TypeError):
            bins = 10
        self._plt.bins(bins)

        # Read overlays
        self._plt.show_mean(self._is_checked("chk-mean"))
        self._plt.show_median(self._is_checked("chk-median"))
        self._plt.show_stats(self._is_checked("chk-stats"))
        self._plt.show_normal(self._is_checked("chk-normal"))

        # Read Y-Axis mode (would affect histogram normalization)
        y_axis_set = self.query_one("#y-axis-radio", RadioSet)
        # index 0 = Frequency, 1 = Probabilistic
        # (In a real implementation, this would toggle density=True/False)

        # Read fallback
        fallback_set = self.query_one("#fallback-radio", RadioSet)
        fallback_map = {
            0: PlotFallback.PLOTWIDGET,
            1: PlotFallback.SIXEL,
            2: PlotFallback.MATPLOTLIB,
        }

        pressed_index = self._get_radioset_index(fallback_set)
        new_fallback = fallback_map.get(pressed_index, PlotFallback.PLOTWIDGET)

        # Update the plot container
        plot_container = self.query_one("#plot-container", PlotContainer)
        plot_container.fallback_mode = new_fallback.value

    def _is_checked(self, radio_id: str) -> bool:
        """Check if a specific RadioButton is pressed (value=True)."""
        try:
            rb = self.query_one(f"#{radio_id}", RadioButton)
            return rb.value
        except Exception:
            return False

    def _get_radioset_index(self, radio_set: RadioSet) -> int:
        """Return the index of the currently pressed button in a RadioSet."""
        try:
            return radio_set.pressed_index
        except Exception:
            return 0


class SimpleLineApp(App[None]):
    """
    Minimal example: just shows a line plot using PlotCallback.
    Demonstrates the simplest usage pattern without any UI controls.
    """

    CSS = """
    #plot-area {
        width: 100%;
        height: 100%;
        padding: 1;
    }
    """

    def compose(self) -> ComposeResult:
        """Compose a header, the plot widget, and a footer."""
        yield Header()

        # Create the plot callback
        plt = PlotCallback(fallback=PlotFallback.PLOTWIDGET)
        plt.axis("x", [1, 2, 3, 4, 5])
        plt.axis("y", [1, 4, 9, 16, 25])
        plt.title("y = x²")

        with Container(id="plot-area"):
            yield plt.widget()

        yield Footer()


class MultiBackendDemoApp(App[None]):
    """
    Demonstrates switching between all three backends dynamically.
    Shows three buttons at the top; clicking a button changes the backend
    used by the PlotContainer below.
    """

    CSS = """
    #controls {
        height: 5;
        width: 100%;
        align: center middle;
        padding: 1;
    }

    #controls Button {
        margin: 0 1;
    }

    #demo-plot-area {
        width: 100%;
        height: 1fr;
        border: round $accent;
        padding: 1;
    }

    .info-bar {
        height: 3;
        text-align: center;
        padding: 1;
        background: $surface;
    }
    """

    def __init__(self) -> None:
        """
        Initialize a PlotCallback with a line plot.
        The fallback can be changed at runtime via the UI buttons.
        """
        super().__init__()
        self._plt = (
            PlotCallback(fallback=PlotFallback.PLOTWIDGET)
            .x([0, 1, 2, 3, 4, 5, 6, 7, 8, 9])
            .y([0, 1, 4, 9, 16, 25, 36, 49, 64, 81])
            .title("Quadratic Function")
            .xlabel("x")
            .ylabel("x²")
            .plot_type(PlotType.LINE)
            .show_mean(True)
            .color("coral")
        )

    def compose(self) -> ComposeResult:
        """Build the UI: header, backend selector buttons, info bar, and plot area."""
        yield Header()

        with Center(id="controls"):
            yield Button("PlotWidget", id="btn-plotwidget", variant="primary")
            yield Button("Sixel (Chafa)", id="btn-sixel", variant="warning")
            yield Button("Matplotlib", id="btn-matplotlib", variant="error")

        yield Static(
            f"Current backend: {self._plt.fallback.value}",
            id="info-bar",
            classes="info-bar",
        )

        with Container(id="demo-plot-area"):
            yield PlotContainer(self._plt, id="demo-container")

        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle backend‑switch button clicks and update the plot container."""
        backend_map = {
            "btn-plotwidget": PlotFallback.PLOTWIDGET,
            "btn-sixel": PlotFallback.SIXEL,
            "btn-matplotlib": PlotFallback.MATPLOTLIB,
        }

        if event.button.id in backend_map:
            new_backend = backend_map[event.button.id]
            info = self.query_one("#info-bar", Static)
            info.update(f"Current backend: {new_backend.value}")

            container = self.query_one("#demo-container", PlotContainer)
            container.fallback_mode = new_backend.value


# ─── Package __init__.py ────────────────────────────────────────────

# __init__.py
"""
textual_plot_callback - A multi-backend plotting system for Textual.

Usage:
    from textual_plot_callback import PlotCallback, PlotFallback, PlotType

    plt = PlotCallback(fallback=PlotFallback.PLOTWIDGET)
    plt.axis("x", [1, 2, 3])
    plt.axis("y", [1, 4, 9])

    # In your Textual compose():
    yield plt.widget()
"""

from plot_callback import (
    PlotCallback,
    PlotFallback,
    PlotType,
    PlotData,
)
from widgets.plot_container import PlotContainer

__all__ = [
    "PlotCallback",
    "PlotFallback",
    "PlotType",
    "PlotData",
    "PlotContainer",
]


if __name__ == "__main__":
    import sys

    demo = sys.argv[1] if len(sys.argv) > 1 else "histogram"

    if demo == "simple":
        SimpleLineApp().run()
    elif demo == "multi":
        MultiBackendDemoApp().run()
    else:
        HistogramApp().run()
