#!/usr/bin/env python3
"""
JSON to Excel-like Table Viewer using Textual
Supports arrow key navigation, cell editing, and saving
"""

import json
import csv
import sys
import re
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from textual.app import App, ComposeResult
from textual.widgets import DataTable, Input, Static, Footer, Button, Label
from textual.containers import Container, Horizontal, Vertical
from textual.binding import Binding
from textual.screen import ModalScreen
from textual.theme import Theme
from rich.text import Text
from assets.themes.crimson_demon import LoadTheme
from assets.services.config_loader import LoadConfig
from assets.services.file_change_observer import FileObserver


class MessageBox(ModalScreen[None]):
    """Message Box (used for notif)"""
    
    BINDINGS = [
        Binding("escape", "dismiss_box", "Close"),
        Binding("enter", "dismiss_box", "Close"),
    ]
    
    def __init__(self, title: str, message: str, msg_type: str = "info"):
        super().__init__()
        self.msg_title = title
        self.message = message
        self.msg_type = msg_type  # info, success, error, warning
    
    def compose(self) -> ComposeResult:
        with Container(id="msg-dialog", classes=f"msg-{self.msg_type}"):
            yield Label(self.msg_title, id="msg-title")
            yield Label(self.message, id="msg-content")
            yield Button("OK", variant="primary", id="ok-btn")
    
    def on_mount(self) -> None:
        self.query_one("#ok-btn", Button).focus()
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss(None)
    
    def action_dismiss_box(self) -> None:
        self.dismiss(None)


class EditCellScreen(ModalScreen[str]):
    """Modal screen for editing a cell value"""
    
    BINDINGS = [
        Binding("escape", "cancel", "Cancel"),
    ]
    
    def __init__(self, current_value: str, column_name: str):
        super().__init__()
        self.current_value = current_value
        self.column_name = column_name
    
    def compose(self) -> ComposeResult:
        with Container(id="edit-dialog"):
            yield Label(f"Edit '{self.column_name}'", id="edit-label")
            yield Input(value=self.current_value, id="edit-input")
            with Horizontal(id="button-container"):
                yield Button("Save", variant="primary", id="save-btn")
                yield Button("Cancel", id="cancel-btn")
    
    def on_mount(self) -> None:
        input_widget = self.query_one("#edit-input", Input)
        input_widget.focus()
        input_widget.cursor_position = len(self.current_value)
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "save-btn":
            input_widget = self.query_one("#edit-input", Input)
            self.dismiss(input_widget.value)
        else:
            self.dismiss(None)
    
    def on_input_submitted(self, event: Input.Submitted) -> None:
        self.dismiss(event.value)
    
    def action_cancel(self) -> None:
        self.dismiss(None)


class ConfirmScreen(ModalScreen[bool]):
    """Confirmation dialog screen"""
    
    BINDINGS = [
        Binding("escape", "cancel", "Cancel"),
        Binding("y", "confirm", "Yes"),
        Binding("n", "cancel", "No"),
    ]
    
    def __init__(self, title: str, message: str):
        super().__init__()
        self.msg_title = title
        self.message = message
    
    def compose(self) -> ComposeResult:
        with Container(id="confirm-dialog"):
            yield Label(self.msg_title, id="confirm-title")
            yield Label(self.message, id="confirm-content")
            with Horizontal(id="button-container"):
                yield Button("Yes", variant="warning", id="yes-btn")
                yield Button("No", id="no-btn")
    
    def on_mount(self) -> None:
        self.query_one("#no-btn", Button).focus()
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss(event.button.id == "yes-btn")
    
    def action_confirm(self) -> None:
        self.dismiss(True)
    
    def action_cancel(self) -> None:
        self.dismiss(False)


class JSONTableViewer(App):
    """This is where the viewer JSON to Excel-like format happen"""
    
    CSS = """
    Screen {
        background: $background;
    }

    /* Modal screens - transparent background, centered content */
    ModalScreen {
        background: transparent;
        align: center middle;
    }

    /* Message Box Dialog */
#msg-dialog {
        width: 40;
        height: auto;
        max-height: 12;
        background: $background;
        border: solid $foreground;
    }

#msg-dialog.msg-success {
        border: solid $success;
    }

#msg-dialog.msg-error {
        border: solid $error;
    }

#msg-dialog.msg-warning {
        border: solid $warning;
    }

#msg-dialog.msg-info {
        border: solid $accent;
    }

#msg-title {
        width: 100%;
        height: 1;
        color: $foreground;
        text-style: bold;
        text-align: center;
        margin-bottom: 1;
    }

#msg-content {
        width: 100%;
        height: auto;
        color: $text-muted;
        text-align: center;
        margin-bottom: 1;
    }

#msg-dialog #ok-btn {
        width: 100%;
        min-width: 10;
    }

    /* Edit Dialog */
#edit-dialog {
        width: 40;
        height: auto;
        max-height: 10;
        background: $surface;
        border: solid $primary;
    }

#edit-label {
        width: 100%;
        height: 1;
        color: $primary;
        text-style: bold;
        text-align: center;
    }

#edit-input {
        width: 100%;
        height: 3;
        background: $background;
        border: solid $secondary;
        color: $foreground;
    }

#edit-input:focus {
        border: solid $primary;
    }

#button-container {
        width: 100%;
        height: 3;
        align: center middle;
    }

#button-container Button {
        min-width: 10;
    }

    /* Confirm Dialog */
#confirm-dialog {
        width: 36;
        height: auto;
        max-height: 10;
        background: $surface;
        border: solid $warning;
        padding: 1 2;
    }

#confirm-title {
        width: 100%;
        height: 1;
        color: $warning;
        text-style: bold;
        text-align: center;
        margin-bottom: 1;
    }

#confirm-content {
        width: 100%;
        height: auto;
        color: $text-muted;
        text-align: center;
        margin-bottom: 1;
    }

    /* Button Variants */
    Button {
        background: $secondary;
        color: $foreground;
        border: none;
    }

    Button:hover {
        background: $panel;
    }

    Button:focus {
        background: $surface;
    }

    Button.-primary {
        background: $primary;
        color: $foreground;
    }

    Button.-primary:hover {
        background: $foreground;
        color: $primary;
    }

    Button.-primary:focus {
        background: $primary 70%;
    }

    Button.-warning {
        background: $warning 20%;
        color: $warning;
    }

    Button.-warning:hover {
        background: $warning 30%;
    }

    /* Main Layout */
#main-container {
        background: $background;
        width: 100%;
    }

    DataTable {
        background: $background;
        height: 100%;
        scrollbar-background: $panel;
        scrollbar-color: $secondary;
        scrollbar-color-hover: $surface;
        scrollbar-color-active: $primary;
    }

    DataTable > .datatable--header {
        background: $background;
        color: $primary;
        text-style: bold;
    }

    DataTable > .datatable--cursor {
        background: $foreground;
        color: $primary;
    }

    DataTable > .datatable--hover {
        background: $primary 30%;
    }

    DataTable > .datatable--even-row {
        background: $surface;
    }

    DataTable > .datatable--odd-row {
        background: $background;
    }

    /* Status Bar */
#status-container {
        dock: bottom;
        height: 2;
        width: 100%;
        background: $panel;
        layout: horizontal;
    }

#status-message {
        width: 1fr;
        height: 1;
        color: $primary;
        padding: 0 1;
        content-align: left middle;
    }

#save-status {
        width: auto;
        min-width: 14;
        height: 1;
        padding: 0 1;
        text-align: right;
        content-align: right middle;
    }

#save-status.saved {
        color: $success;
        background: $success 20%;
    }

#save-status.unsaved {
        color: $error;
        background: $error 20%;
    }

    /* Title Bar */
#title-bar {
        dock: top;
        height: 3;
        background: $surface;
        color: $primary;
        text-align: center;
        padding: 1;
        border-bottom: solid $secondary;
    }

    /* Footer */
    Footer {
        background: $background;
    }

    Footer > .footer--key {
        background: $primary 20%;
        color: $primary;
    }

    Footer > .footer--description {
        color: $success;
    }
    """
    
    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("enter", "edit_cell", "Edit Cell"),
        Binding("e", "edit_cell", "Edit"),
        Binding("s", "save", "Save"),
        Binding("ctrl+s", "save", "Save", show=False),
        Binding("r", "reload", "Reload"),
        Binding("a", "add_row", "Add Row"),
        Binding("d", "delete_row", "Delete Row"),
        Binding("<Esc>", "deselect", "Deselect"),
    ]

    POLL_INTERVAL = 1.0 # How many seconds to check if file is changed?
    
    def __init__(self, json_file: str):
        super().__init__()
        self.json_file = Path(json_file)
        self.data: List[Dict[str, Any]] = []
        self.columns: List[str] = []
        self.modified = False
        self.custom_formats: List[Dict[str, Any]] = []  # ADD THIS
        self._last_mtime: float | None = None
        LoadConfig(self)

    
    def compose(self) -> ComposeResult:
        yield Static(
            f"ready.\n",
            id="title-bar"
        )
        with Container(id="main-container"):
            yield DataTable(id="json-table", cursor_type="cell", zebra_stripes=True)
        with Horizontal(id="status-container"):
            yield Static("Ready", id="status-message")
            yield Static("● Saved", id="save-status", classes="saved")
        yield Footer()
    
    def on_mount(self) -> None:
        """Called when the app is mounted."""
        LoadTheme(self)
        self.load_json()
        self.set_interval(self.POLL_INTERVAL, self._poll_file_changes) # Starts polling... for each one second
        self.title = f"JSON Viewer - {self.json_file.name}"
    
    # TODO: Not sure yet how to refactor this, and so is the config.
    def _format_cell_value(self, value: str, column_name: str) -> Union[Text, str]:
        """Apply custom formatting to a cell value based on config rules."""
        if not self.custom_formats:
            return value
        
        column_lower = column_name.lower()
        
        for fmt in self.custom_formats:
            # Check if this format applies to this column
            target_columns = [c.lower() for c in fmt.get("for_columns", [])]
            
            if column_lower not in target_columns:
                continue
            
            # Check if regex matches
            pattern = fmt.get("_compiled")
            if pattern and pattern.match(value):
                # Create styled text
                styled = Text(value)
                
                # Build style string
                style_parts = []
                
                if fmt.get("color"):
                    style_parts.append(fmt["color"])
                
                if fmt.get("bold", False):
                    style_parts.append("bold")
                
                if fmt.get("italic", False):
                    style_parts.append("italic")
                
                if fmt.get("underline", False):
                    style_parts.append("underline")
                
                if fmt.get("bgcolor"):
                    style_parts.append(f"on {fmt['bgcolor']}")
                
                if style_parts:
                    styled.stylize(" ".join(style_parts))
                
                return styled
        
        return value
        
    def _update_save_status(self) -> None:
        """Update the save status indicator."""
        save_status = self.query_one("#save-status", Static)
        if self.modified:
            save_status.update("● Unsaved")
            save_status.remove_class("saved")
            save_status.add_class("unsaved")
        else:
            save_status.update("● Saved")
            save_status.remove_class("unsaved")
            save_status.add_class("saved")
    
    def _show_message(self, title: str, message: str, msg_type: str = "info") -> None:
        """Show a message box."""
        self.push_screen(MessageBox(title, message, msg_type))
    
    def load_json(self) -> None:
        """Load the JSON file and populate the table."""
        try:

            suffix = self.json_file.suffix.lower()

            if suffix == ".json":

                with open(self.json_file, "r", encoding="utf-8") as f:
                    content = f.read()
                    content = self._fix_json(content)
                    self.data = json.loads(content)

                if not isinstance(self.data, list):
                    self.data = [self.data]

            elif suffix == ".csv":

                with open(self.json_file, "r", encoding="utf-8", newline="") as f:
                    reader = csv.DictReader(f)

                    self.data = [
                        dict(row)
                        for row in reader
                    ]

            else:
                raise ValueError(
                    f"Unsupported file type: {suffix}"
                )

            self._populate_table()

            self._update_status(
                f"Loaded {len(self.data)} entries"
            )

            self.modified = False
            self._update_save_status()

            # self.show_message(
            #     "File Loaded",
            #     f"Loaded {len(self.data)} entries\nfrom {self.json_file.name}",
            #     "success"
            # )
            
            # Track modifiation time
            # BUG: Whenever the file is s(aved), the code assumes it is EXTERNALLY changed.
            self._last_mtime = os.path.getmtime(self.json_file)

        except FileNotFoundError:

            self._update_status("File not found!")

            self._show_message(
                "Error",
                f"File not found:\n{self.json_file}",
                "error"
            )

        except json.JSONDecodeError as e:

            self._update_status("Invalid JSON")

            self._show_message(
                "JSON Error",
                f"Invalid JSON:\n{str(e)[:30]}",
                "error"
            )

        except csv.Error as e:

            self._update_status("Invalid CSV")

            self._show_message(
                "CSV Error",
                f"Invalid CSV:\n{str(e)[:30]}",
                "error"
            )

        except Exception as e:

            self._update_status(f"Error: {e}")

            self._show_message(
                "Error",
                str(e)[:50],
                "error"
            )

    
    def _reload_file(self) -> None:
        """Re-run load_data on the current file."""
        if self.json_file:
            now = datetime.now().strftime("%H:%M:%S")
            self.load_json()
            self.notify(f"🔄 File reloaded at {now}", severity="information")
    
    def _poll_file_changes(self) -> None:
        """Check if loaded file was modified externally."""
        if not self.json_file or not os.path.exists(self.json_file):
            return

        current_mtime = os.path.getmtime(self.json_file)

        if self._last_mtime is not None and current_mtime != self._last_mtime:
            self._last_mtime = current_mtime
            self._reload_file()
    def _fix_json(self, content: str) -> str:
        """Attempt to fix common JSON issues."""
        content = re.sub(r',\s*]', ']', content)
        content = re.sub(r',\s*}', '}', content)
        content = re.sub(r'(\{|,)\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*:', r'\1"\2":', content)
        return content
    
    def _populate_table(self) -> None:
        """Populate the DataTable with JSON data."""
        table = self.query_one("#json-table", DataTable)
        table.clear(columns=True)
        
        if not self.data:
            self._update_status("No data to display")
            return
        
        self.columns = ["entry"]
        for item in self.data:
            if isinstance(item, dict):
                for key in item.keys():
                    if key not in self.columns:
                        self.columns.append(key)
        
        for col in self.columns:
            table.add_column(col.upper(), key=col)
        
        for idx, item in enumerate(self.data, 1):
            row_data = [Text(str(idx), style="#888888")]  # Entry column styled gray
            if isinstance(item, dict):
                for col in self.columns[1:]:
                    value = item.get(col, "")
                    str_value = str(value) if value is not None else ""
                    # Apply custom formatting
                    formatted_value = self._format_cell_value(str_value, col)
                    row_data.append(formatted_value)
            else:
                row_data.append(str(item))
                row_data.extend([""] * (len(self.columns) - 2))
            table.add_row(*row_data, key=str(idx))
        
        table.focus()
    
    def _update_status(self, message: str) -> None:
        """Update the status bar with a message."""
        status = self.query_one("#status-message", Static)
        cell_info = ""
        
        try:
            table = self.query_one("#json-table", DataTable)
            if table.cursor_coordinate:
                row = table.cursor_coordinate.row + 1
                col = table.cursor_coordinate.column + 1
                col_name = self.columns[table.cursor_coordinate.column] if table.cursor_coordinate.column < len(self.columns) else ""
                cell_info = f" │ R{row}C{col} ({col_name})"
        except Exception:
            pass
        
        status.update(f"{message}{cell_info}")
    
    def on_data_table_cell_highlighted(self, event: DataTable.CellHighlighted) -> None:
        """Called when a cell is highlighted."""
        self._update_status(f"Value: {event.value}")
    
    def action_edit_cell(self) -> None:
        """Edit the currently selected cell."""
        table = self.query_one("#json-table", DataTable)
        
        if table.cursor_coordinate is None:
            self._show_message("Warning", "No cell selected", "warning")
            return
        
        row_idx = table.cursor_coordinate.row
        col_idx = table.cursor_coordinate.column
        
        if col_idx == 0:
            self._show_message("Warning", "Entry column is\nread-only", "warning")
            return
        
        try:
            current_value = str(table.get_cell_at(table.cursor_coordinate))
            column_name = self.columns[col_idx] if col_idx < len(self.columns) else f"Column {col_idx}"
        except Exception as e:
            self._show_message("Error", f"Cannot read cell:\n{e}", "error")
            return
        
        def on_edit_complete(new_value: Optional[str]) -> None:
            if new_value is not None and new_value != current_value:
                table.update_cell_at(table.cursor_coordinate, new_value)
                
                if row_idx < len(self.data):
                    data_col = self.columns[col_idx]
                    self.data[row_idx][data_col] = new_value
                    self.modified = True
                    self._update_save_status()
                    self._update_status(f"Updated {column_name}")
                    
                    self._show_message(
                        "Cell Updated",
                        f"{column_name}:\n'{new_value}'",
                        "success"
                    )
        
        self.push_screen(EditCellScreen(current_value, column_name), on_edit_complete)
    
    def action_save(self) -> None:
        """Save changes back to the JSON file."""
        if not self.modified:
            self._show_message("Info", "No changes to save", "info")
            return
        
        try:
            with open(self.json_file, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
            self.modified = False
            self._update_save_status()
            self._update_status("File saved")
            self._show_message(
                "Saved",
                f"Saved to:\n{self.json_file.name}",
                "success"
            )
        except PermissionError:
            self._show_message("Error", "Permission denied", "error")
        except Exception as e:
            self._show_message("Error", f"Save failed:\n{str(e)[:30]}", "error")
    
    def action_reload(self) -> None:
        """Reload the JSON file from disk."""
        if self.modified:
            def on_confirm(confirmed: bool) -> None:
                if confirmed:
                    self.modified = False
                    self._update_save_status()
                    self.load_json()
            
            self.push_screen(
                ConfirmScreen("Reload File", "Discard changes?"),
                on_confirm
            )
        else:
            self.load_json()
    
    def action_add_row(self) -> None:
        """Add a new row at the end."""
        new_entry = {}
        for col in self.columns[1:]:
            new_entry[col] = ""
        
        self.data.append(new_entry)
        self.modified = True
        self._update_save_status()
        self._populate_table()
        
        table = self.query_one("#json-table", DataTable)
        table.move_cursor(row=len(self.data) - 1, column=1)
        
        self._update_status(f"Added row {len(self.data)}")
        self._show_message(
            "Row Added",
            f"Entry {len(self.data)} created",
            "success"
        )
    
    def action_delete_row(self) -> None:
        """Delete the currently selected row."""
        table = self.query_one("#json-table", DataTable)
        
        if table.cursor_coordinate is None:
            self._show_message("Warning", "No row selected", "warning")
            return
        
        row_idx = table.cursor_coordinate.row
        
        if row_idx >= len(self.data):
            self._show_message("Error", "Invalid row", "error")
            return
        
        def on_confirm(confirmed: bool) -> None:
            if confirmed:
                del self.data[row_idx]
                self.modified = True
                self._update_save_status()
                self._populate_table()
                self._update_status(f"Deleted row")
                self._show_message(
                    "Deleted",
                    f"Row {row_idx + 1} removed",
                    "success"
                )
        
        self.push_screen(
            ConfirmScreen("Delete Row", f"Delete row {row_idx + 1}?"),
            on_confirm
        )
    
    def action_deselect(self) -> None:
        """Deselect current cell."""
        self._update_status("Ready")
    
    def action_quit(self) -> None:
        """Quit the application with confirmation if modified."""
        if self.modified:
            def on_confirm(confirmed: bool) -> None:
                if confirmed:
                    self.exit()
            
            self.push_screen(
                ConfirmScreen("Quit", "Exit without saving?"),
                on_confirm
            )
        else:
            self.exit()

def create_sample_json(filename: str) -> None:
    """Create a sample JSON file for testing."""
    sample_data = [
        {"date": "5/4/26", "nominal": "25", "description": "Initial deposit"},
        {"date": "5/5/26", "nominal": "50", "description": "Second payment"},
        {"date": "5/6/26", "nominal": "100", "description": "Third payment"},
        {"date": "5/7/26", "nominal": "75", "description": "Fourth payment"},
        {"date": "5/8/26", "nominal": "200", "description": "Final payment"},
    ]
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(sample_data, f, indent=2)
    
    print(f"Created sample file: {filename}")


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("=" * 45)
        print("  JSON Table Viewer - Excel-like Editor")
        print("=" * 45)
        print("\nUsage:")
        print("  python json_viewer.py <file.json>")
        print("  python json_viewer.py --sample")
        print("\nKeybindings:")
        print("  ↑↓←→      Navigate cells")
        print("  Enter/E   Edit cell")
        print("  S         Save file")
        print("  R         Reload file")
        print("  A         Add row")
        print("  D         Delete row")
        print("  Q         Quit")
        sys.exit(1)
    
    if sys.argv[1] == "--sample":
        create_sample_json("sample.json")
        print("Run: python json_viewer.py sample.json")
        sys.exit(0)
    
    json_file = sys.argv[1]
    
    if not Path(json_file).exists():
        print(f"Error: File '{json_file}' not found!")
        sys.exit(1)
    
    app = JSONTableViewer(json_file)
    app.run()


if __name__ == "__main__":
    main()
