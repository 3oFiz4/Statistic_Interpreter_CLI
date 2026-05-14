import numpy as np
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Container, Vertical
from textual.widgets import (
    Static,
    RadioSet,
    RadioButton,
    Input,
)
from textual import on
from textual_plot import PlotWidget
from .drop_box import DropBox
from .input_box import InputBox
from .radio_group import RadioGroup
from .accordion import Accordion
from textual.widget import Widget
from .plot_engine.plot_callback import PlotCallback, PlotFallback, PlotType
from .plot_engine.widgets.plot_container import PlotContainer

def _generate_normal_distribution(
    mean: float = 50.0,
    std: float = 10.0,
    n: int = 200,
    seed: int = 42,
) -> list[float]:
    """Generate normally distributed sample data."""
    rng = np.random.default_rng(seed)
    return rng.normal(loc=mean, scale=std, size=n).tolist()

#TODO: Add different graph depending on each items
# Default: Normal distribution with mean=50, std=10, n=200
SAMPLE_HISTOGRAM_DATA = _generate_normal_distribution(mean=50.0, std=10.0, n=200)

class Histogram(Widget):

    CSS = """
    Horizontal {
        height: 100%;
    }

    #sidebar {
        width: 1fr;
        padding: 1;
        border: solid gray;
    }

    #main {
        width: 4fr;
        padding: 1;
        border: solid gray;
    }

    .section {
        margin-bottom: 1;
    }

    RadioSet {
        margin-top: 1;
    }

    Input {
        margin-top: 1;
    }

    .title {
        margin-bottom: 1;
        text-style: bold;
        text-align:center;
    }
    """

    def __init__(
        self,
        data: list[float] | None = None,
        *,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        super().__init__(name=name, id=id, classes=classes)
        self._data = data if data is not None else SAMPLE_HISTOGRAM_DATA
        
        self._plt = (
            PlotCallback(fallback=PlotFallback.PLOTWIDGET)
            .plot_type(PlotType.HISTOGRAM)
            .y(self._data)
            .title("Histogram")
            .xlabel("Value")
            .ylabel("Frequency")
            .bins(10)
            .show_mean(True)
            .color("steelblue")
        )

    def compose(self) -> ComposeResult:
            # Sidebar
            with Accordion("Histogram", id="histogram-accordion"):
                with Horizontal():
                    with Container(id="sidebar"):
                        with Vertical():
                            # Y Axis
                            yield RadioGroup(
                                label="Y-Axis",
                                options=["Frequency", "Probabilistic"],
                                default="Probabilistic",
                                id="Y-Axis",
                            )
                            # Show Dropdown
                            yield DropBox(
                                label="Show",
                                options=[
                                    "Mean",
                                    "Median",
                                    "Statistics",
                                    "Normal Distribution",
                                ],
                                selected=["Mean"],
                                id="show-dropdown",
                            )
                            # Bin Size Input
                            yield InputBox(label="Bin size", placeholder="type here...", id="bin-size")
                            yield RadioGroup(
                                label="_fallback",
                                options=["Plotext", "Sixel (heavy)", "Matplotlib" ],
                                default="Plotext",
                                id="_fallback",
                            )

                    # Main Content
                    with Container(id="main"):
                        with Container(id="plot-area"):
                            yield Static(
                                f"Current backend: {self._plt.fallback.value}",
                                id="info-bar",
                                classes="info-bar",
                            )
                            yield PlotContainer(self._plt, id="plot-container")

# ── Event Handlers ──────────────────────────────────────────────

    @on(RadioGroup.Changed)
    def _on_fallback_changed(self, event) -> None:
        """Immediately switch render mode when radio changes."""
        fallback_map = {
            "Plotext": PlotFallback.PLOTWIDGET,
            "Sixel (heavy)": PlotFallback.SIXEL,
            "Matplotlib": PlotFallback.MATPLOTLIB,
        }
        
        new_fallback = fallback_map[event.value]

        plot_container = self.query_one("#plot-container", PlotContainer)

        plot_container.fallback_mode = new_fallback.value
        plot_container._rebuild()

    @on(RadioGroup.Changed)
    def _on_y_axis_changed(self, event) -> None:
        """Handle Y-Axis mode change (Frequency vs Probabilistic)."""
        # You could add density support to PlotCallback if needed
        # For now, just trigger a rebuild
        pass

    def on_button_pressed(self, event) -> None:
        """Handle Apply button click."""
        if event.button.id == "apply-btn":
            self._apply_settings()

    def _apply_settings(self) -> None:
        """Read sidebar controls and update the plot."""
        
        # Get bin size
        try:
            bin_input = self.query_one("#bin-size", InputBox)
            bin_value = bin_input.value.strip() if hasattr(bin_input, 'value') else ""
            bins = int(bin_value) if bin_value else 10
        except (ValueError, Exception):
            bins = 10
        
        self._plt.bins(bins)

        # Get show options
        try:
            show_dropdown = self.query_one("#show-dropdown", DropBox)
            selected = show_dropdown.selected if hasattr(show_dropdown, 'selected') else []
            
            self._plt.show_mean("Mean" in selected)
            self._plt.show_median("Median" in selected)
            self._plt.show_stats("Statistics" in selected)
            self._plt.show_normal("Normal Distribution" in selected)
        except Exception:
            pass

        # Rebuild the plot with new settings
        try:
            plot_container = self.query_one("#plot-container", PlotContainer)
            plot_container._rebuild()
        except Exception:
            pass

    def set_data(self, data: list[float]) -> None:
        """Update histogram data externally."""
        self._data = data
        self._plt.y(data)
        
        try:
            plot_container = self.query_one("#plot-container", PlotContainer)
            plot_container.update_data(y=data)
        except Exception:
            pass
