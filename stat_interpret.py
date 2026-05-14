"""
Statistical Interpreter - A Textual-based application for interpreting .json and .csv files.
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

from assets.themes.crimson_demon import LoadTheme

from assets.services.file_loader import FileLoader
from assets.services.measurement_classifer import MeasurementClassifier
from assets.services.statistics_engine import StatisticsEngine
from assets.services.file_change_observer import FileObserver


from assets.widgets.drop_box import DropBox
from assets.widgets.radio_group import RadioGroup
from assets.widgets.input_box import InputBox
from assets.widgets.graph import Histogram

# ============================================================================
# Process: FileLoader -> MeasurementClassifier -> StatisticsEngine
# ============================================================================

# ============================================================================
# POSITION: Place this class in a separate file like `checkbox_panel.py`
# Usage: from checkbox_panel import CheckboxPanel
# ============================================================================
class CheckboxPanel(Widget):
    """A toggleable panel of checkboxes."""

    class SelectionChanged(Message):
        def __init__(self, panel_id: str, selected: list[str]) -> None:
            super().__init__()
            self.panel_id = panel_id
            self.selected = selected

    def __init__(self, panel_id: str, items: list[str], initially_selected: list[str] | None = None, **kwargs):
        super().__init__(**kwargs)
        self.panel_id = panel_id
        self.items = items
        self._selected: set[str] = set(initially_selected or items)

    def compose(self) -> ComposeResult:
        with VerticalScroll(classes="cb-panel", id=f"panel-{self.panel_id}"):
            for item in self.items:
                yield Checkbox(item, value=item in self._selected, id=f"cb-{self.panel_id}-{item.replace(' ', '_')}")

    @on(Checkbox.Changed)
    def on_checkbox_changed(self, event: Checkbox.Changed) -> None:
        label = str(event.checkbox.label)
        if event.value:
            self._selected.add(label)
        else:
            self._selected.discard(label)
        self.post_message(self.SelectionChanged(self.panel_id, list(self._selected)))

    def get_selected(self) -> list[str]:
        return list(self._selected)

    def toggle_visibility(self) -> bool:
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


# ============================================================================
# POSITION: Main application class - Place in `stat_app.py`
# Usage: from stat_app import StatisticalInterpreterApp
# ============================================================================
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

    selected_metric_keys: reactive[list[str]] = reactive(list, always_update=True)
    selected_ordinal_keys: reactive[list[str]] = reactive(list, always_update=True)
    selected_nominal_keys: reactive[list[str]] = reactive(list, always_update=True)
    selected_stats: reactive[list[str]] = reactive(list, always_update=True)
    
    POLL_INTERVAL = 1.0 # How many seconds to check if file is changed?
    
    def __init__(self, filepath: str = "", **kwargs):
        super().__init__(**kwargs)
        self.filepath = filepath
        self.file_loader: Optional[FileLoader] = None
        self.classifier: Optional[MeasurementClassifier] = None
        self.engine = StatisticsEngine()
        self._stats_options = ["Mean", "Median", "Mode", "Sum", "Variance", "STDV", "Minimum", "Maximum", "Range", "Quartile 1", "Quartile 2", "Quartile 3", "IQR", "Median Absolute Deviation", "Skew", "Kurtosis", "n", "95% CI", "Mean +- Std.", "Count Unique", "Count Missing", "Percentage Missing", "First Quartile Spread", "Third Quartile Spread", "Median Difference", "Midrange", "Quartile Deviation", "Central 50% Range", "Central 80% Range", "Percentile 10", "Percentile 90", "Lower Outlier Boundary", "Upper Outlier Boundary", "Outlier Values", "Outlier Count", "Coefficient of Variation", "Mean Absolute Deviation", "Trimmed Mean", "Spread Score", "Range Percentage", "Interval Width", "Bin Count", "Data Span", "Duplicate Count", "Data Density", "Positive Count", "Negative Count", "Zero Count", "Even Count", "Odd Count", "Above Mean Count", "Below Mean Count", "Closest to Mean", "Farthest from Mean", "Lower Half Mean", "Upper Half Mean", "Data Balance", "Symmetry Score", "Normalized Mean", "Normalized STDV", "Peak Density", "Data Uniformity", "Value Concentration"]        
        self._stats_default_options = ["Mean", "Median", "Mode", "Sum", "Variance", "STDV", "Minimum", "Maximum", "Range", "Quartile 1", "Quartile 2", "Quartile 3", "IQR", "Median Absolute Deviation", "Skew", "Kurtosis", "n", "95% CI", "Mean +- Std."]        

        self._active_buttons: dict[str, bool] = {}
        self._last_mtime: float | None = None

    def on_mount(self) -> None:
        if self.filepath:
            LoadTheme(self) # Crimson Demon Theme
            self.load_data(self.filepath)
            self.set_interval(self.POLL_INTERVAL, self._poll_file_changes) # Starts polling... for each one second
        # else:
            # TODO: Add a Message that shows how to use the script properly.

    def compose(self) -> ComposeResult:
        with VerticalScroll(id="main-container"):
            yield Label("", id="file-info", classes="file-info")

            with Container(classes="measurement-container", id="meas-section"):
                yield Label("Level of Measurement", classes="section-title")
                with Horizontal(classes="btn-row", id="meas-btns"):
                    yield DropBox(
                        label="Metric",
                        options=[],
                        selected=[],
                        id="metric-dropdown",
                    )
                    yield DropBox(
                        label="Ordinal",
                        options=[],
                        selected=[],
                        id="ordinal-dropdown",
                    )
                    yield DropBox(
                        label="Nominal",
                        options=[],
                        selected=[],
                        id="nominal-dropdown",
                    )

            with Container(classes="stats-container", id="stats-section"):
                yield Label("Descriptive Statistics", classes="section-title")
                with Horizontal(classes="btn-row"):
                    yield DropBox(
                        label="Process",
                        options=[],
                        selected=[],
                        id="stats-dropdown",
                    )

            with Container(classes="results-container"):
                yield Label("Results", classes="section-title")
                yield DataTable(id="results-table", zebra_stripes=True)

            with Vertical():
                yield Histogram()

            # with Container(classes="freq-container"):
            #     yield Label("Frequency Table", classes="section-title")
            #     yield DataTable(id="freq-table", zebra_stripes=True)

        yield Footer()

    def on_file_selected(self, filepath: str) -> None:
        if filepath:
            self.load_data(filepath)

    def load_data(self, filepath: str) -> None:
        try:
            self.file_loader = FileLoader(filepath)
            self.classifier = MeasurementClassifier(self.file_loader)
            self.filepath = filepath
            
            # Track modifiation time
            self._last_mtime = os.path.getmtime(filepath)

            file_info = self.query_one("#file-info", Label)
            file_info.update(f"File: {Path(filepath).name} | Rows: {self.file_loader.row_count()} | Cols: {len(self.file_loader.keys)}")

            self._rebuild_panels()
            self._update_results_table()

            
        except Exception as e:
            self.notify(f"Error: {e}", severity="error")


    # ---- NEW: reload method ----
    def _reload_file(self) -> None:
        """Re-run load_data on the current file."""
        if self.filepath:
            now = datetime.now().strftime("%H:%M:%S")
            self.load_data(self.filepath)
            self.notify(f"🔄 File reloaded at {now}", severity="information")

    def _poll_file_changes(self) -> None:
        """Check if loaded file was modified externally."""
        if not self.filepath or not os.path.exists(self.filepath):
            return

        current_mtime = os.path.getmtime(self.filepath)

        if self._last_mtime is not None and current_mtime != self._last_mtime:
            self._last_mtime = current_mtime
            self._reload_file()

    def _rebuild_panels(self) -> None:
        if not self.classifier:
            return

        metric_keys = self.classifier.get_metric_keys()
        ordinal_keys = self.classifier.get_ordinal_keys()
        nominal_keys = self.classifier.get_nominal_keys()

        # Update dropdowns
        self.query_one("#metric-dropdown", DropBox).set_options(metric_keys, metric_keys)
        self.query_one("#ordinal-dropdown", DropBox).set_options(ordinal_keys, ordinal_keys)
        self.query_one("#nominal-dropdown", DropBox).set_options(nominal_keys, nominal_keys)
        stats_dropdown = self.query_one("#stats-dropdown", DropBox)

        # Keep selected lists in sync
        self.selected_metric_keys = metric_keys.copy()
        self.selected_ordinal_keys = ordinal_keys.copy()
        self.selected_nominal_keys = nominal_keys.copy()

        # Stats panel stays as CheckboxPanel
        self.query_one("#stats-dropdown", DropBox).set_options(self._stats_options, self._stats_default_options)
        
        self.selected_stats = self._stats_default_options.copy()


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

    def _update_results_table(self) -> None:
        if not self.file_loader or not self.classifier:
            return

        table = self.query_one("#results-table", DataTable)
        table.clear(columns=True)

        if not self.selected_stats:
            return

        table.add_column("Key", key="key")
        table.add_column("Level", key="level")
        for stat in self.selected_stats:
            table.add_column(stat, key=stat.lower())

        def fmt(v: Any) -> str:
            if v is None:
                return "—"
            if isinstance(v, float):
                return f"{v:.4f}" if v != int(v) else str(int(v))
            return str(v)

        for key in self.selected_metric_keys:
            values = self.file_loader.get_numeric_column(key)
            stats = self.engine.compute_metric_stats(values, self.selected_stats)
            row = [key, "Metric"] + [fmt(stats.get(s)) for s in self.selected_stats]
            table.add_row(*row)

        for key in self.selected_ordinal_keys:
            values = self.file_loader.get_column(key)
            stats = self.engine.compute_ordinal_stats(values, self.selected_stats)
            row = [key, "Ordinal"] + [fmt(stats.get(s)) for s in self.selected_stats]
            table.add_row(*row)

        for key in self.selected_nominal_keys:
            values = self.file_loader.get_column(key)
            stats = self.engine.compute_nominal_stats(values, self.selected_stats)
            row = [key, "Nominal"] + [fmt(stats.get(s)) for s in self.selected_stats]
            table.add_row(*row)

def main():
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
