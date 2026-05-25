"""
Statistical Interpreter – a Textual‑based GUI for loading, classifying,
and computing descriptive statistics on .json or .csv data files.

The application flow is:
    1. Load the file with :class:`FileLoader`.
    2. Determine each column’s level of measurement using
       :class:`MeasurementClassifier`.
    3. Compute requested statistics via :class:`StatisticsEngine`.

The UI consists of three dropdowns (Metric, Ordinal, Nominal) for selecting
columns, a dropdown for choosing which statistics to display, and a
results table that updates automatically when selections change.  The
application also watches the source file for external modifications and
reloads it automatically.
"""

from __future__ import annotations

import os
from pathlib import Path
import sys
from typing import Any, Optional
from datetime import datetime

from textual import on
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.css.query import NoMatches
from textual.message import Message
from textual.reactive import reactive
from textual.screen import ModalScreen
from textual.widget import Widget
from textual.widgets import (
    Button,
    Checkbox,
    DataTable,
    Footer,
    Header,
    Input,
    Label,
    Select,
    Static,
)

# t loader (crimson demon theme)
from assets.themes.crimson_demon import LoadTheme

# Core services
from assets.services.statistics.file_loader import FileLoader
from assets.services.statistics.measurement_classifer import MeasurementClassifier
from assets.services.statistics.statistics_engine import StatisticsEngine
from assets.services.statistics.file_change_observer import FileObserver

# Custom widgets
from assets.widgets.statistics.drop_box import DropBox
from assets.widgets.statistics.radio_group import RadioGroup
from assets.widgets.statistics.input_box import InputBox
from assets.widgets.statistics.graph import Histogram


# Helper widget: a panel of checkboxes that notifies when its selection changes
class CheckboxPanel(Widget):
    """A toggleable panel of checkboxes."""

    class SelectionChanged(Message):
        """Message emitted when the set of selected checkboxes changes."""

        def __init__(self, panel_id: str, selected: list[str]) -> None:
            super().__init__()
            self.panel_id = panel_id
            self.selected = selected

    def __init__(
        self,
        panel_id: str,
        items: list[str],
        initially_selected: list[str] | None = None,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.panel_id = panel_id
        self.items = items
        # Store selected items in a set for O(1) add/remove operations
        self._selected: set[str] = set(initially_selected or items)

    def compose(self) -> ComposeResult:
        """Create a vertical scroll container with a checkbox for each item."""
        with VerticalScroll(classes="cb-panel", id=f"panel-{self.panel_id}"):
            for item in self.items:
                # Pre‑select items that are in the initial set
                yield Checkbox(
                    item,
                    value=item in self._selected,
                    id=f"cb-{self.panel_id}-{item.replace(' ', '_')}",
                )

    @on(Checkbox.Changed)
    def on_checkbox_changed(self, event: Checkbox.Changed) -> None:
        """Update the internal set and emit a SelectionChanged message."""
        label = str(event.checkbox.label)
        if event.value:
            self._selected.add(label)
        else:
            self._selected.discard(label)
        self.post_message(self.SelectionChanged(self.panel_id, list(self._selected)))

    def get_selected(self) -> list[str]:
        """Return the current list of selected items."""
        return list(self._selected)

    def toggle_visibility(self) -> bool:
        """Show/hide the panel and return the new visibility state."""
        try:
            panel = self.query_one(f"#panel-{self.panel_id}")
            if panel.has_class("-visible"):
                panel.remove_class("-visible")
                return False
            else:
                panel.add_class("-visible")
                return True
        except NoMatches:
            return False


# ---------------------------------------------------------------------------
# Main Textual application
# ---------------------------------------------------------------------------
class StatisticalInterpreterApp(App):
    """Main Textual application for statistical interpretation."""

    TITLE = "Statistical Interpreter"
    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("t", "cycle_theme", "Theme"),
        Binding("r", "refresh", "Refresh"),
        Binding("o", "open_file", "Open"),
    ]
    DEFAULT_CSS = """
    .measurement-container {
        height: auto;
        padding: 0;
        margin: 0;
    }

    .stats-container {
        height: auto;
        padding: 0;
        margin: 0;
    }

    .btn-row {
        height: auto;
        padding: 0;
        margin: 0;
    }
    """

    # Reactive state – automatically triggers UI updates when changed
    selected_metric_keys: reactive[list[str]] = reactive(list, always_update=True)
    selected_ordinal_keys: reactive[list[str]] = reactive(list, always_update=True)
    selected_nominal_keys: reactive[list[str]] = reactive(list, always_update=True)
    selected_stats: reactive[list[str]] = reactive(list, always_update=True)

    POLL_INTERVAL = 1.0  # seconds between file‑change checks

    def __init__(self, filepath: str = "", **kwargs):
        """Initialize the app and core services."""
        super().__init__(**kwargs)
        self.filepath = filepath
        self.file_loader: Optional[FileLoader] = None
        self.classifier: Optional[MeasurementClassifier] = None
        self.engine = StatisticsEngine()
        # Full list of supported statistics (displayed in the stats dropdown)
        self._stats_options = [
            "Mean",
            "Median",
            "Mode",
            "Sum",
            "Variance",
            "STDV",
            "Minimum",
            "Maximum",
            "Range",
            "Quartile 1",
            "Quartile 2",
            "Quartile 3",
            "IQR",
            "Median Absolute Deviation",
            "Skew",
            "Kurtosis",
            "n",
            "95% CI",
            "Mean +- Std.",
            "Count Unique",
            "Count Missing",
            "Percentage Missing",
            "First Quartile Spread",
            "Third Quartile Spread",
            "Median Difference",
            "Midrange",
            "Quartile Deviation",
            "Central 50% Range",
            "Central 80% Range",
            "Percentile 10",
            "Percentile 90",
            "Lower Outlier Boundary",
            "Upper Outlier Boundary",
            "Outlier Values",
            "Outlier Count",
            "Coefficient of Variation",
            "Mean Absolute Deviation",
            "Trimmed Mean",
            "Spread Score",
            "Range Percentage",
            "Interval Width",
            "Bin Count",
            "Data Span",
            "Duplicate Count",
            "Data Density",
            "Positive Count",
            "Negative Count",
            "Zero Count",
            "Even Count",
            "Odd Count",
            "Above Mean Count",
            "Below Mean Count",
            "Closest to Mean",
            "Farthest from Mean",
            "Lower Half Mean",
            "Upper Half Mean",
            "Data Balance",
            "Symmetry Score",
            "Normalized Mean",
            "Normalized STDV",
            "Peak Density",
            "Data Uniformity",
            "Value Concentration",
        ]
        # Default stats shown when a file is first loaded
        self._stats_default_options = [
            "Mean",
            "Median",
            "Mode",
            "Sum",
            "Variance",
            "STDV",
            "Minimum",
            "Maximum",
            "Range",
            "Quartile 1",
            "Quartile 2",
            "Quartile 3",
            "IQR",
            "Median Absolute Deviation",
            "Skew",
            "Kurtosis",
            "n",
            "95% CI",
            "Mean +- Std.",
        ]

        self._active_buttons: dict[str, bool] = {}
        self._last_mtime: float | None = None

    # -----------------------------------------------------------------------
    # Lifecycle hooks
    # -----------------------------------------------------------------------
    def on_mount(self) -> None:
        """Run after the UI is mounted – load file (if provided) and start polling."""
        if self.filepath:
            LoadTheme(self)  # Apply the Crimson Demon theme
            self.load_data(self.filepath)
            self.set_interval(self.POLL_INTERVAL, self._poll_file_changes)

    def compose(self) -> ComposeResult:
        """Build the UI layout."""
        with VerticalScroll(id="main-container"):
            yield Label("", id="file-info", classes="file-info")

            # Measurement selection section
            with Container(classes="measurement-container", id="meas-section"):
                yield Label("Level of Measurement", classes="section-title")
                with Horizontal(classes="btn-row", id="meas-btns"):
                    yield DropBox(label="Metric", options=[], selected=[], id="metric-dropdown")
                    yield DropBox(label="Ordinal", options=[], selected=[], id="ordinal-dropdown")
                    yield DropBox(label="Nominal", options=[], selected=[], id="nominal-dropdown")

            # Statistics selection section
            with Container(classes="stats-container", id="stats-section"):
                yield Label("Descriptive Statistics", classes="section-title")
                with Horizontal(classes="btn-row"):
                    yield DropBox(label="Process", options=[], selected=[], id="stats-dropdown")

            # Results table
            with Container(classes="results-container"):
                yield Label("Results", classes="section-title")
                yield DataTable(id="results-table", zebra_stripes=True)

            # Histogram widget (placeholder for future visualizations)
            with Vertical():
                yield Histogram()

        yield Footer()

    # -----------------------------------------------------------------------
    # File handling
    # -----------------------------------------------------------------------
    def on_file_selected(self, filepath: str) -> None:
        """Callback when a file is chosen via the UI."""
        if filepath:
            self.load_data(filepath)

    def load_data(self, filepath: str) -> None:
        """Load the data file, classify columns, and refresh UI."""
        try:
            self.file_loader = FileLoader(filepath)
            self.classifier = MeasurementClassifier(self.file_loader)
            self.filepath = filepath

            # Store modification time for change detection
            self._last_mtime = os.path.getmtime(filepath)

            # Update file info banner
            file_info = self.query_one("#file-info", Label)
            file_info.update(
                f"File: {Path(filepath).name} | Rows: {self.file_loader.row_count()} | Cols: {len(self.file_loader.keys)}"
            )

            # Rebuild dropdown panels and results table
            self._rebuild_panels()
            self._update_results_table()

        except Exception as e:
            self.notify(f"Error: {e}", severity="error")

    # -----------------------------------------------------------------------
    # Auto‑reload support
    # -----------------------------------------------------------------------
    def _reload_file(self) -> None:
        """Re‑run ``load_data`` on the current file and notify the user."""
        if self.filepath:
            now = datetime.now().strftime("%H:%M:%S")
            self.load_data(self.filepath)
            self.notify(f"🔄 File reloaded at {now}", severity="information")

    def _poll_file_changes(self) -> None:
        """Periodically check the file's modification time and reload if changed."""
        if not self.filepath or not os.path.exists(self.filepath):
            return

        current_mtime = os.path.getmtime(self.filepath)

        if self._last_mtime is not None and current_mtime != self._last_mtime:
            self._last_mtime = current_mtime
            self._reload_file()

    # -----------------------------------------------------------------------
    # UI update helpers
    # -----------------------------------------------------------------------
    def _rebuild_panels(self) -> None:
        """Populate dropdowns with column names and set default selections."""
        if not self.classifier:
            return

        metric_keys = self.classifier.get_metric_keys()
        ordinal_keys = self.classifier.get_ordinal_keys()
        nominal_keys = self.classifier.get_nominal_keys()

        # Update the three measurement dropdowns
        self.query_one("#metric-dropdown", DropBox).set_options(metric_keys, metric_keys)
        self.query_one("#ordinal-dropdown", DropBox).set_options(ordinal_keys, ordinal_keys)
        self.query_one("#nominal-dropdown", DropBox).set_options(nominal_keys, nominal_keys)

        # Keep reactive selections in sync with the UI
        self.selected_metric_keys = metric_keys.copy()
        self.selected_ordinal_keys = ordinal_keys.copy()
        self.selected_nominal_keys = nominal_keys.copy()

        # Populate the statistics dropdown
        self.query_one("#stats-dropdown", DropBox).set_options(
            self._stats_options, self._stats_default_options
        )
        self.selected_stats = self._stats_default_options.copy()

    # -----------------------------------------------------------------------
    # Event handlers for dropdown changes
    # -----------------------------------------------------------------------
    @on(DropBox.Changed, "#metric-dropdown")
    def on_metric_selection_changed(self, event: DropBox.Changed) -> None:
        self.selected_metric_keys = event.selected
        self._update_results_table()

    @on(DropBox.Changed, "#ordinal-dropdown")
    def on_ordinal_selection_changed(self, event: DropBox.Changed) -> None:
        self.selected_ordinal_keys = event.selected
        self._update_results_table()

    @on(DropBox.Changed, "#nominal-dropdown")
    def on_nominal_selection_changed(self, event: DropBox.Changed) -> None:
        self.selected_nominal_keys = event.selected
        self._update_results_table()

    @on(DropBox.Changed, "#stats-dropdown")
    def on_stats_dropdown_changed(self, event: DropBox.Changed) -> None:
        self.selected_stats = event.selected
        self._update_results_table()

    # -----------------------------------------------------------------------
    # Table rendering
    # -----------------------------------------------------------------------
    def _update_results_table(self) -> None:
        """Re‑populate the results DataTable based on current selections."""
        if not self.file_loader or not self.classifier:
            return

        table = self.query_one("#results-table", DataTable)
        table.clear(columns=True)

        if not self.selected_stats:
            return

        # Fixed columns
        table.add_column("Key", key="key")
        table.add_column("Level", key="level")
        # Dynamic statistic columns
        for stat in self.selected_stats:
            table.add_column(stat, key=stat.lower())

        def fmt(v: Any) -> str:
            """Format a value for display in the table."""
            if v is None:
                return "—"
            if isinstance(v, float):
                return f"{v:.4f}" if v != int(v) else str(int(v))
            return str(v)

        # Metric columns – numeric stats
        for key in self.selected_metric_keys:
            values = self.file_loader.get_numeric_column(key)
            stats = self.engine.compute_metric_stats(values, self.selected_stats)
            row = [key, "Metric"] + [fmt(stats.get(s)) for s in self.selected_stats]
            table.add_row(*row)

        # Ordinal columns – treat as generic values
        for key in self.selected_ordinal_keys:
            values = self.file_loader.get_column(key)
            stats = self.engine.compute_ordinal_stats(values, self.selected_stats)
            row = [key, "Ordinal"] + [fmt(stats.get(s)) for s in self.selected_stats]
            table.add_row(*row)

        # Nominal columns – treat as generic values
        for key in self.selected_nominal_keys:
            values = self.file_loader.get_column(key)
            stats = self.engine.compute_nominal_stats(values, self.selected_stats)
            row = [key, "Nominal"] + [fmt(stats.get(s)) for s in self.selected_stats]
            table.add_row(*row)


def main() -> None:
    """Entry point – parse command‑line argument and launch the app."""
    filepath = ""
    if len(sys.argv) > 1:
        filepath = sys.argv[1]
        if not os.path.isfile(filepath):
            print(f"File not found: {filepath}")
            sys.exit(1)
        if Path(filepath).suffix.lower() not in (".json", ".csv"):
            print("Use .json or .csv")
            sys.exit(1)
    app = StatisticalInterpreterApp(filepath=filepath)
    app.run()


if __name__ == "__main__":
    main()
