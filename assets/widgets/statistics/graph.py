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

# ----------------------------------------------------------------------
# Helper: generate a synthetic normal distribution.
# This function is used to provide default data for the histogram
# when the user does not supply their own dataset.
# ----------------------------------------------------------------------
def _generate_normal_distribution(
    mean: float = 50.0,
    std: float = 10.0,
    n: int = 200,
    seed: int = 42,
) -> list[float]:
    """Generate normally distributed sample data.

    Parameters
    ----------
    mean: float
        The mean (center) of the distribution.
    std: float
        The standard deviation (spread) of the distribution.
    n: int
        Number of random samples to generate.
    seed: int
        Seed for reproducibility.

    Returns
    -------
    list[float]
        A list of `n` floating‑point numbers drawn from the specified normal
        distribution.
    """
    rng = np.random.default_rng(seed)
    return rng.normal(loc=mean, scale=std, size=n).tolist()

# Default dataset used by the widget when no external data is provided.
SAMPLE_HISTOGRAM_DATA = _generate_normal_distribution(mean=50.0, std=10.0, n=200)

# ----------------------------------------------------------------------
# Histogram widget
# ----------------------------------------------------------------------
class Histogram(Widget):
    """
    A Textual widget that displays an interactive histogram.

    The UI is split into a sidebar (controls) and a main area (plot).
    Users can adjust the number of bins, toggle statistical overlays,
    and switch between different rendering back‑ends (Plotext, Sixel,
    Matplotlib) on the fly.
    """

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
        """
        Initialise the histogram widget.

        Parameters
        ----------
        data: list[float] | None
            Optional list of values to plot. If omitted, a synthetic
            normal distribution is used.
        name, id, classes:
            Standard Textual widget identifiers.
        """
        super().__init__(name=name, id=id, classes=classes)
        # Use provided data or fall back to the sample data.
        self._data = data if data is not None else SAMPLE_HISTOGRAM_DATA

        # Configure the PlotCallback with default settings.
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

    # ------------------------------------------------------------------
    # Layout composition
    # ------------------------------------------------------------------
    def compose(self) -> ComposeResult:
        """
        Build the widget hierarchy.

        The layout consists of:
        * An Accordion titled "Histogram" that contains the whole UI.
        * A Horizontal container splitting the view into a sidebar and main area.
        * The sidebar holds controls: Y‑axis mode, overlay toggles, bin size,
          and backend selector.
        * The main area shows the current backend label and the PlotContainer.
        """
        # Sidebar
        with Accordion("Histogram", id="histogram-accordion"):
            with Horizontal():
                with Container(id="sidebar"):
                    with Vertical():
                        # Y Axis mode selector
                        yield RadioGroup(
                            label="Y-Axis",
                            options=["Frequency", "Probabilistic"],
                            default="Probabilistic",
                            id="Y-Axis",
                        )
                        # Overlay options dropdown
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
                        # Bin size input box
                        yield InputBox(label="Bin size", placeholder="type here...", id="bin-size")
                        # Backend selector
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

    # ------------------------------------------------------------------
    # Event handlers
    # ------------------------------------------------------------------

    @on(RadioGroup.Changed)
    def _on_fallback_changed(self, event) -> None:
        """
        Switch the rendering backend when the user selects a different option.

        The RadioGroup emits a `Changed` message with the selected value.
        This handler maps the textual label to the corresponding PlotFallback
        enum, updates the PlotContainer, and forces a rebuild.
        """
        fallback_map = {
            "Plotext": PlotFallback.PLOTWIDGET,
            "Sixel (heavy)": PlotFallback.SIXEL,
            "Matplotlib": PlotFallback.MATPLOTLIB,
        }

        new_fallback = fallback_map[event.value]

        plot_container = self.query_one("#plot-container", PlotContainer)

        # Update the fallback mode on the container and rebuild the plot.
        plot_container.fallback_mode = new_fallback.value
        plot_container._rebuild()

    @on(RadioGroup.Changed)
    def _on_y_axis_changed(self, event) -> None:
        """
        Placeholder for handling Y‑axis mode changes (Frequency vs Probabilistic).

        Currently no additional logic is required; the method exists for
        future extension and to keep the UI responsive.
        """
        # Future implementation could adjust PlotCallback to show density.
        pass

    def on_button_pressed(self, event) -> None:
        """
        Handle button presses within the widget.

        Currently only an "Apply" button (if added later) would trigger
        `_apply_settings`. The check guards against unrelated button events.
        """
        if event.button.id == "apply-btn":
            self._apply_settings()

    def _apply_settings(self) -> None:
        """
        Read all sidebar controls and apply them to the PlotCallback.

        This includes:
        * Bin size (validated integer, defaults to 10)
        * Which statistical overlays to show (Mean, Median, etc.)
        * Rebuilding the plot to reflect the new configuration.
        """
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
        """
        Update the histogram data from an external source.

        Parameters
        ----------
        data: list[float]
            New dataset to visualise.
        """
        self._data = data
        self._plt.y(data)

        try:
            plot_container = self.query_one("#plot-container", PlotContainer)
            plot_container.update_data(y=data)
        except Exception:
            pass
