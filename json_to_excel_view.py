# Required modules
import json
import csv
import os
import re
import copy
from pathlib import Path
from datetime import datetime
from collections import deque
from typing import Any, Dict, List, Optional, Set, Tuple, Union

# Textual modules
from textual import on
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical
from textual.coordinate import Coordinate
from textual.screen import Screen
from textual.widgets import (
    Button,
    DataTable,
    Footer,
    Input,
    Label,
    Static,
    Switch,
)
from rich.text import Text

# Widgets modules
from assets.widgets.viewer.clipboard import Clipboard
from assets.widgets.viewer.confirmation_box import ConfirmScreen
from assets.widgets.viewer.message_box import MessageBox
from assets.widgets.viewer.edit_cell import EditCellScreen
from assets.widgets.viewer.add_column import AddColumnScreen
from assets.widgets.viewer.find_replace import FindReplaceScreen
from assets.themes.crimson_demon import LoadTheme
from assets.widgets.viewer.formatter import (
    build_default_config,
    apply_rules,
    RuleContext,
    FormatRule,          # only needed if rules added at runtime
    TableFormattingConfig,
)

#> Configurable Variables
MAX_UNDO_HISTORY = 50       # max number of undo states kept in memory
MIN_COLUMN_WIDTH  = 3       # min column width in characters
MAX_COLUMN_WIDTH  = 60      # max column width in characters
DEFAULT_COL_WIDTH = 12      # width start for newly added columns



#> MAIN APP STARTS HERE
class JsonTableApp(App):
    """
    Keybind Pattern (remember it)
    ------------------
    * Single letters   -> common quick actions (edit, add, delete …)
    * Ctrl+letter      -> power actions (save, copy, paste, undo …)
    * Alt+letter       -> structural changes (insert col, hide col …)
    * Function keys    -> find/replace, resize, sort …
    * Arrow / PgUp …   -> navigation (delegated to DataTable where possible)
    """

    CSS = """
Screen { background: $background; }

    /* Modal screens – transparent background, centered content */
    ModalScreen { background: transparent; align: center middle; }

    /* Message Box Dialog */
    #msg-dialog {
        width: 40; height: auto; max-height: 12;
        background: $background; border: solid $foreground;
    }
    #msg-dialog.msg-success { border: solid $success; }
    #msg-dialog.msg-error   { border: solid $error;   }
    #msg-dialog.msg-warning{ border: solid $warning; }
    #msg-dialog.msg-info   { border: solid $accent;  }

    #msg-title   { width:100%; height:1; color:$foreground; text-style:bold; text-align:center; margin-bottom:1; }
    #msg-content { width:100%; height:auto; color:$text-muted; text-align:center; margin-bottom:1; }
    #msg-dialog #ok-btn { width:100%; min-width:10; }

    /* Edit Dialog */
    #edit-dialog {
        width: 40; height: auto; max-height: 10;
        background: $surface; border: solid $primary;
    }
    #edit-label { width:100%; height:1; color:$primary; text-style:bold; text-align:center; }
    #edit-input {
        width:100%; height:3; background:$background; border: solid $secondary; color:$foreground;
    }
    #edit-input:focus { border: solid $primary; }
    #button-container { width:100%; height:3; align:center middle; }
    #button-container Button { min-width:10; }

    /* Confirm Dialog */
    #confirm-dialog {
        width:36; height:auto; max-height:10;
        background:$surface; border: solid $warning; padding:1 2;
    }
    #confirm-title   { width:100%; height:1; color:$warning; text-style:bold; text-align:center; margin-bottom:1; }
    #confirm-content { width:100%; height:auto; color:$text-muted; text-align:center; margin-bottom:1; }

    /* Button variants */
    Button { background:$secondary; color:$foreground; border:none; }
    Button:hover { background:$panel; }
    Button:focus { background:$surface; }
    Button.-primary { background:$primary; color:$foreground; }
    Button.-primary:hover { background:$foreground; color:$primary; }
    Button.-primary:focus { background:$primary 70%; }
    Button.-warning { background:$warning 20%; color:$warning; }
    Button.-warning:hover { background:$warning 30%; }

    /* Main layout */
    #main-container { background:$background; width:100%; }
    DataTable {
        background:$background; height:100%;
        scrollbar-background:$panel; scrollbar-color:$secondary;
        scrollbar-color-hover:$surface; scrollbar-color-active:$primary;
    }
    DataTable > .datatable--header { background:$background; color:$primary; text-style:bold; }
    DataTable > .datatable--cursor { background:$foreground; color:$primary; }
    DataTable > .datatable--hover  { background:$primary 30%; }
    DataTable > .datatable--even-row { background:$surface; }
    DataTable > .datatable--odd-row  { background:$background; }

    /* Status bar */
    #status-container { dock:bottom; height:2; width:100%; background:$panel; layout:horizontal; }
    #status-message { width:1fr; height:1; color:$primary; padding:0 1; content-align:left middle; }
    #save-status { width:auto; min-width:14; height:1; padding:0 1; text-align:right; content-align:right middle; }
    #save-status.saved   { color:$success; background:$success 20%; }
    #save-status.unsaved { color:$error;   background:$error 20%; }

    /* Title bar */
    #title-bar { dock:top; height:3; background:$surface; color:$primary; text-align:center; padding:1; border-bottom: solid $secondary; }

    /* Footer */
    Footer { background:$background; }
    Footer > .footer--key { background:$primary 20%; color:$primary; }
    Footer > .footer--description { color:$success; }
    """
    
    #TODO: This is excel like keybind.. Thought of switching to nvim keybinds lately.
    # if you dont like nvim idc :sob:, just get used to it bruhhh
    BINDINGS = [
Binding("q",          "quit",              "Quit"),
Binding("w",         "save",              "Save"),
Binding("r",         "reload",            "Reload"),
Binding("escape",     "deselect",          "Deselect / Cancel"),

# NAV (nvim-style hjkl)
Binding("l",          "next_cell",         "Next Cell",   show=False),
Binding("h",          "prev_cell",         "Prev Cell",   show=False),
Binding("0",        "goto_first_cell",   "First Cell",  show=False),
Binding("G",    "goto_last_cell",    "Last Cell",   show=False),
Binding("$",          "jump_right",        "Jump Right",  show=False),
Binding("^",          "jump_left",         "Jump Left",   show=False),

# EDIT
Binding("enter",      "edit_cell",         "Edit Cell"),
Binding("i",          "edit_cell",         "Edit",        show=False),
Binding("d",          "clear_cell",        "Clear Cell"),
Binding("u",          "undo",              "Undo"),
Binding("ctrl+r",     "redo",              "Redo"),

# CRUD Row
Binding("a",          "add_row",           "Add Row"),
# Binding("D",        "delete_row",        "Delete Row"),
Binding("O",          "insert_row_above",  "Insert Above"),
Binding("o",          "insert_row_below",  "Insert Below"),
# Binding("Y",        "duplicate_row",     "Duplicate Row"),

# CRUD Column
Binding("ctrl+a",   "add_column",        "Add Column"),
Binding("ctrl+d",   "delete_column",     "Delete Column"),
Binding("ctrl+h",   "insert_col_left",   "Insert Col Left"),
Binding("ctrl+l",   "insert_col_right",  "Insert Col Right"),

# MOVE Row
Binding("alt+k",    "move_row_up",       "Move Row Up"),
Binding("alt+j",    "move_row_down",     "Move Row Down"),

# YANK & PASTE
Binding("y",          "copy_cell",         "Copy Cell"),
Binding("Y",        "copy_row",          "Copy Row"),
Binding("D",        "cut_row",           "Cut Row"),
Binding("p",          "paste",             "Paste"),

# SELECT
Binding("V",        "select_all",        "Select All"),
Binding("v",          "select_row",        "Select Row"),

# HIDE & UNHIDE
Binding(".",        "hide_row",          "Hide Row"),
Binding(";",        "unhide_all_rows",   "Unhide All Rows"),
Binding("/",        "hide_column",       "Hide Column"),
Binding("'",        "unhide_all_columns","Unhide All Cols"),

# RESIZE Column
Binding(">",          "widen_column",      "Widen Col"),
Binding("<",          "narrow_column",     "Narrow Col"),
Binding("=",          "autofit_column",    "Auto-fit Col"),

# SORT
Binding("s",        "sort_asc",          "Sort ↑"),
Binding("S",        "sort_desc",         "Sort ↓"),

# FIND & REPLACE
Binding("?",          "find_replace",      "Find & Replace"),
    ]

    POLL_INTERVAL = 1.0   # the interval between checking the file if there is an external change. For example, say you are checking file main.json, the moment it changes, it is updated 1 sec (default) after.
    
    def __init__(self, json_file: str) -> None:
        super().__init__()
        self.json_file = Path(json_file)

        #  core
        self.data:    List[Dict[str, Any]] = []
        self.columns: List[str]            = []   # first entry is always "entry"
        self.modified = False

        #  column metadata
        self.column_widths: Dict[str, int]  = {}  # col_name -> char width
        self.hidden_columns: Set[str]        = set()
        self.hidden_rows:    Set[int]        = set()  # zero-based data indices

        #  clipboard & undo
        self.board_clip:   Clipboard       = Clipboard()
        self._undo_stack: deque           = deque(maxlen=MAX_UNDO_HISTORY)
        self._redo_stack: deque           = deque(maxlen=MAX_UNDO_HISTORY)

        #  misc
        self.custom_formats: List[Dict[str, Any]] = []
        self._last_mtime:    float | None          = None
        self._fmt_cfg = build_default_config()   # ← add this one line

    def compose(self) -> ComposeResult: # ui
        yield Static("", id="title-bar")
        with Container(id="main-container"):
            yield DataTable(id="json-table", cursor_type="cell", zebra_stripes=True)
        with Horizontal(id="status-container"):
            yield Static("Ready", id="status-message")
            yield Static("● Saved", id="save-status", classes="saved")
        yield Footer()

    def on_mount(self) -> None:
        self.load_json()
        LoadTheme(self)  # apply the Crimson Demon theme, burrrnnnns
        self.set_interval(self.POLL_INTERVAL, self._poll_file_changes)
        self.title = f"Viewer – {self.json_file.name}"

    # HELPFER FUNC. Labelled as _
    def _push_undo(self) -> None:
        """Remember the current data, and then hidden sets into the undo stack"""
        snapshot = {
            "data":           copy.deepcopy(self.data),
            "columns":        list(self.columns),
            "column_widths":  dict(self.column_widths),
            "hidden_columns": set(self.hidden_columns),
            "hidden_rows":    set(self.hidden_rows),
        }
        self._undo_stack.append(snapshot)
        self._redo_stack.clear()   # new action invalidates redo history

    def _restore_snapshot(self, snap: dict) -> None:
        """Append snapshot dict to current state and then refresh the table"""
        self.data           = copy.deepcopy(snap["data"])
        self.columns        = list(snap["columns"])
        self.column_widths  = dict(snap["column_widths"])
        self.hidden_columns = set(snap["hidden_columns"])
        self.hidden_rows    = set(snap["hidden_rows"])
        self.modified       = True
        self._update_save_status()
        self._populate_table()

    # Chapter actions: undo / redo

    def action_undo(self) -> None:
        if not self._undo_stack:
            self._show_message("Undo", "Nothing to undo", "info")
            return
        # Remember current state to redo stack
        self._redo_stack.append({
            "data":           copy.deepcopy(self.data),
            "columns":        list(self.columns),
            "column_widths":  dict(self.column_widths),
            "hidden_columns": set(self.hidden_columns),
            "hidden_rows":    set(self.hidden_rows),
        })
        self._restore_snapshot(self._undo_stack.pop())
        self._update_status("Undo")

    def action_redo(self) -> None:
        if not self._redo_stack:
            self._show_message("Redo", "Nothing to redo", "info")
            return
        self._undo_stack.append({
            "data":           copy.deepcopy(self.data),
            "columns":        list(self.columns),
            "column_widths":  dict(self.column_widths),
            "hidden_columns": set(self.hidden_columns),
            "hidden_rows":    set(self.hidden_rows),
        })
        self._restore_snapshot(self._redo_stack.pop())
        self._update_status("Redo")

    # Chapter actions: navigation

    def action_next_cell(self) -> None:
        """Tab -> move one cell to the right, then wrap to next row"""
        table = self.query_one("#json-table", DataTable)
        row, col = table.cursor_coordinate.row, table.cursor_coordinate.column
        col += 1
        if col >= len(self.columns):
            col  = 0
            row += 1
        if row < table.row_count:
            table.move_cursor(row=row, column=col)

    def action_prev_cell(self) -> None:
        """Shift+Tab -> move one cell to the left, then wrap to previous row"""
        table = self.query_one("#json-table", DataTable)
        row, col = table.cursor_coordinate.row, table.cursor_coordinate.column
        col -= 1
        if col < 0:
            col  = len(self.columns) - 1
            row -= 1
        if row >= 0:
            table.move_cursor(row=row, column=col)

    def action_goto_first_cell(self) -> None:
        self.query_one("#json-table", DataTable).move_cursor(row=0, column=0)

    def action_goto_last_cell(self) -> None:
        table = self.query_one("#json-table", DataTable)
        table.move_cursor(row=table.row_count - 1, column=len(self.columns) - 1)

    def action_jump_right(self) -> None:
        """Ctrl+Right -? jump to the last non-empty cell to the right"""
        table = self.query_one("#json-table", DataTable)
        row, col = table.cursor_coordinate.row, table.cursor_coordinate.column
        target = len(self.columns) - 1
        # scan for last non-empty
        for c in range(col + 1, len(self.columns)):
            val = str(table.get_cell_at(Coordinate(row, c)))
            if val.strip():
                target = c
        table.move_cursor(row=row, column=target)

    def action_jump_left(self) -> None:
        """Ctrl+Left -> jump to the first non-empty cell to the left"""
        table = self.query_one("#json-table", DataTable)
        row, col = table.cursor_coordinate.row, table.cursor_coordinate.column
        target = 0
        for c in range(col - 1, -1, -1):
            val = str(table.get_cell_at(Coordinate(row, c)))
            if val.strip():
                target = c
        table.move_cursor(row=row, column=target)

    # ================================================================== actions: editing

    def action_edit_cell(self) -> None:
        """Open the single-cell editor for the currently highlighted cell"""
        table = self.query_one("#json-table", DataTable)
        if table.cursor_coordinate is None:
            return

        row_idx = table.cursor_coordinate.row
        col_idx = table.cursor_coordinate.column

        # index col. is read-only
        if col_idx == 0:
            self._show_message("Warning", "Entry column is read-only", "warning")
            return

        current_value = str(table.get_cell_at(table.cursor_coordinate))
        column_name   = self.columns[col_idx] if col_idx < len(self.columns) else f"Col{col_idx}"
        coord         = table.cursor_coordinate   # capture before async

        def on_edit_complete(new_value: Optional[str]) -> None:
            if new_value is None or new_value == current_value:
                return
            self._push_undo()
            table.update_cell_at(coord, new_value)
            self.data[row_idx][self.columns[col_idx]] = new_value
            self.modified = True
            self._update_save_status()
            self._update_status(f"Updated {column_name}")

        self.push_screen(EditCellScreen(current_value, column_name), on_edit_complete)

    def action_clear_cell(self) -> None:
        """Delete key -> set current cell to empty string"""
        table = self.query_one("#json-table", DataTable)
        if table.cursor_coordinate is None:
            return
        col_idx = table.cursor_coordinate.column
        if col_idx == 0:
            return   # protect the index column
        row_idx = table.cursor_coordinate.row
        self._push_undo()
        col_name = self.columns[col_idx]
        table.update_cell_at(table.cursor_coordinate, "")
        self.data[row_idx][col_name] = ""
        self.modified = True
        self._update_save_status()
        self._update_status(f"Cleared {col_name}")

    # Chapter actions: row CRUD

    def action_add_row(self) -> None:
        """Append blank row at the end of the dataset"""
        self._push_undo()
        new_entry = {col: "" for col in self.columns[1:]}
        self.data.append(new_entry)
        self._finish_structural_change(f"Added row {len(self.data)}")
        table = self.query_one("#json-table", DataTable)
        table.move_cursor(row=len(self.data) - 1, column=1)

    def action_insert_row_above(self) -> None:
        """Insert a blank row above the current cursor row"""
        table   = self.query_one("#json-table", DataTable)
        row_idx = table.cursor_coordinate.row if table.cursor_coordinate else 0
        self._push_undo()
        self.data.insert(row_idx, {col: "" for col in self.columns[1:]})
        self._finish_structural_change(f"Inserted row at {row_idx + 1}")
        self.query_one("#json-table", DataTable).move_cursor(row=row_idx, column=1)

    def action_insert_row_below(self) -> None:
        """Insert a blank row below the current cursor row"""
        table   = self.query_one("#json-table", DataTable)
        row_idx = (table.cursor_coordinate.row + 1) if table.cursor_coordinate else len(self.data)
        self._push_undo()
        self.data.insert(row_idx, {col: "" for col in self.columns[1:]})
        self._finish_structural_change(f"Inserted row at {row_idx + 1}")
        self.query_one("#json-table", DataTable).move_cursor(row=row_idx, column=1)

    def action_delete_row(self) -> None:
        """Delete the currently highlighted row (with confirmation)"""
        table   = self.query_one("#json-table", DataTable)
        row_idx = table.cursor_coordinate.row if table.cursor_coordinate else None
        if row_idx is None or row_idx >= len(self.data):
            self._show_message("Warning", "No row selected", "warning")
            return

        def on_confirm(confirmed: bool) -> None:
            if confirmed:
                self._push_undo()
                # we remove from hidden-rows set and adjust indices above
                self.hidden_rows = {
                    r if r < row_idx else r - 1
                    for r in self.hidden_rows
                    if r != row_idx
                }
                del self.data[row_idx]
                self._finish_structural_change(f"Deleted row {row_idx + 1}")

        self.push_screen(ConfirmScreen("Delete Row", f"Delete row {row_idx + 1}?"), on_confirm)

    def action_duplicate_row(self) -> None:
        """Ctrl+D -> insert a copy of the current row directly below it"""
        table   = self.query_one("#json-table", DataTable)
        row_idx = table.cursor_coordinate.row if table.cursor_coordinate else None
        if row_idx is None or row_idx >= len(self.data):
            return
        self._push_undo()
        dup = copy.deepcopy(self.data[row_idx])
        self.data.insert(row_idx + 1, dup)
        self._finish_structural_change(f"Duplicated row {row_idx + 1}")
        self.query_one("#json-table", DataTable).move_cursor(row=row_idx + 1, column=1)

    # ================================================================== actions: move rows

    def action_move_row_up(self) -> None:
        """Alt+Up -> swap the current row with the one above it"""
        table   = self.query_one("#json-table", DataTable)
        row_idx = table.cursor_coordinate.row if table.cursor_coordinate else 0
        if row_idx <= 0:
            return
        self._push_undo()
        self.data[row_idx], self.data[row_idx - 1] = self.data[row_idx - 1], self.data[row_idx]
        self._finish_structural_change(f"Moved row {row_idx + 1} up")
        self.query_one("#json-table", DataTable).move_cursor(row=row_idx - 1, column=1)

    def action_move_row_down(self) -> None:
        """Alt+Down -> swap the current row with the one below it"""
        table   = self.query_one("#json-table", DataTable)
        row_idx = table.cursor_coordinate.row if table.cursor_coordinate else 0
        if row_idx >= len(self.data) - 1:
            return
        self._push_undo()
        self.data[row_idx], self.data[row_idx + 1] = self.data[row_idx + 1], self.data[row_idx]
        self._finish_structural_change(f"Moved row {row_idx + 1} down")
        self.query_one("#json-table", DataTable).move_cursor(row=row_idx + 1, column=1)

    # ================================================================== actions: column CRUD

    def action_add_column(self) -> None:
        """Alt+A -> prompt for a name and append a new column"""
        def on_name(name: Optional[str]) -> None:
            if not name:
                return
            if name in self.columns:
                self._show_message("Error", f"Column '{name}' already exists", "error")
                return
            self._push_undo()
            self.columns.append(name)
            self.column_widths[name] = DEFAULT_COL_WIDTH
            for row in self.data:
                row[name] = ""
            self._finish_structural_change(f"Added column '{name}'")

        self.push_screen(AddColumnScreen(), on_name)

    def action_delete_column(self) -> None:
        """Alt+D -> delete the currently focused column (cannot delete 'entry')"""
        table   = self.query_one("#json-table", DataTable)
        col_idx = table.cursor_coordinate.column if table.cursor_coordinate else 0
        if col_idx == 0:
            self._show_message("Warning", "Cannot delete index column", "warning")
            return
        col_name = self.columns[col_idx]

        def on_confirm(confirmed: bool) -> None:
            if confirmed:
                self._push_undo()
                self.columns.remove(col_name)
                self.column_widths.pop(col_name, None)
                self.hidden_columns.discard(col_name)
                for row in self.data:
                    row.pop(col_name, None)
                self._finish_structural_change(f"Deleted column '{col_name}'")

        self.push_screen(ConfirmScreen("Delete Column", f"Delete column '{col_name}'?"), on_confirm)

    def action_insert_col_left(self) -> None:
        """Alt+I -> insert a new column to the left of the current column"""
        table   = self.query_one("#json-table", DataTable)
        col_idx = table.cursor_coordinate.column if table.cursor_coordinate else 1
        col_idx = max(col_idx, 1)   # never insert before "entry"
        self._insert_column_at(col_idx)

    def action_insert_col_right(self) -> None:
        """Alt+Shift+I -> insert a new column to the right of the current column"""
        table   = self.query_one("#json-table", DataTable)
        col_idx = (table.cursor_coordinate.column + 1) if table.cursor_coordinate else len(self.columns)
        col_idx = max(col_idx, 1)
        self._insert_column_at(col_idx)

    def _insert_column_at(self, position: int) -> None:
        def on_name(name: Optional[str]) -> None:
            if not name:
                return
            if name in self.columns:
                self._show_message("Error", f"Column '{name}' exists", "error")
                return
            self._push_undo()
            self.columns.insert(position, name)
            self.column_widths[name] = DEFAULT_COL_WIDTH
            for row in self.data:
                row[name] = ""
            self._finish_structural_change(f"Inserted column '{name}'")

        self.push_screen(AddColumnScreen(), on_name)

    # ================================================================== actions: copy / paste

    def action_copy_cell(self) -> None:
        """Ctrl+C -> copy the current cell's text value to the board_clip"""
        table = self.query_one("#json-table", DataTable)
        if table.cursor_coordinate is None:
            return
        value = str(table.get_cell_at(table.cursor_coordinate))
        self.board_clip.copy_cell(value)
        self._update_status(f"Copied cell: {value!r}")
        self.notify(f"📋 Copied: {value!r}", severity="information")

    def action_copy_row(self) -> None:
        """Ctrl+Shift+C -> copy the entire current row to the board_clip"""
        table   = self.query_one("#json-table", DataTable)
        row_idx = table.cursor_coordinate.row if table.cursor_coordinate else None
        if row_idx is None or row_idx >= len(self.data):
            return
        self.board_clip.copy_row(self.data[row_idx])
        self._update_status(f"Copied row {row_idx + 1}")
        self.notify(f"📋 Row {row_idx + 1} copied", severity="information")

    def action_cut_row(self) -> None:
        """Ctrl+X -> cut the current row (will be removed on paste)"""
        table   = self.query_one("#json-table", DataTable)
        row_idx = table.cursor_coordinate.row if table.cursor_coordinate else None
        if row_idx is None or row_idx >= len(self.data):
            return
        self.board_clip.copy_row(self.data[row_idx], cut=True, index=row_idx)
        self._update_status(f"Cut row {row_idx + 1} (paste to move)")
        self.notify(f"✂️ Row {row_idx + 1} cut", severity="warning")

    def action_paste(self) -> None:
        """Ctrl+V -> paste board_clip contents at the current position"""
        table   = self.query_one("#json-table", DataTable)
        row_idx = table.cursor_coordinate.row if table.cursor_coordinate else len(self.data)
        col_idx = table.cursor_coordinate.column if table.cursor_coordinate else 1

        if self.board_clip.has_cell:
            # ── paste a single cell value ──
            if col_idx == 0:
                self._show_message("Warning", "Cannot paste into index column", "warning")
                return
            self._push_undo()
            col_name  = self.columns[col_idx]
            new_value = self.board_clip.cell_value or ""
            table.update_cell_at(table.cursor_coordinate, new_value)
            self.data[row_idx][col_name] = new_value
            self._update_status(f"Pasted cell: {new_value!r}")

        elif self.board_clip.has_row:
            # ── paste (or move, if cut) a full row ──
            self._push_undo()
            new_row = copy.deepcopy(self.board_clip.row_data)

            if self.board_clip.has_cut_row and self.clipboard.cut_index is not None:
                cut_idx = self.board_clip.cut_index
                # Remove the original cut row first
                if cut_idx < len(self.data):
                    del self.data[cut_idx]
                    # Adjust insertion index if the cut row was above
                    insert_at = row_idx if cut_idx >= row_idx else row_idx - 1
                else:
                    insert_at = row_idx
                self.data.insert(insert_at, new_row)
                self.board_clip.clear()   # cut-paste is a one-shot operation
            else:
                # Plain copy-paste: insert below current row
                self.data.insert(row_idx + 1, new_row)

            self._finish_structural_change("Pasted row")

        else:
            self._show_message("Info", "board_clip is empty", "info")
            return

        self.modified = True
        self._update_save_status()

    # ================================================================== actions: selection

    def action_select_all(self) -> None:
        """Ctrl+A -> visual indicator (DataTable doesn't have multi-select natively)"""
        self._update_status(f"All {len(self.data)} rows / {len(self.columns)} cols")
        self.notify("ℹ️ DataTable shows all rows", severity="information")

    def action_select_row(self) -> None:
        """Space -> highlight the whole row by jumping to column 0"""
        table = self.query_one("#json-table", DataTable)
        if table.cursor_coordinate:
            table.move_cursor(row=table.cursor_coordinate.row, column=0)

    # ================================================================== actions: hide/unhide

    def action_hide_row(self) -> None:
        """Ctrl+H -> hide the current row from view"""
        table   = self.query_one("#json-table", DataTable)
        row_idx = table.cursor_coordinate.row if table.cursor_coordinate else None
        if row_idx is None:
            return
        self._push_undo()
        self.hidden_rows.add(row_idx)
        self._finish_structural_change(f"Hidden row {row_idx + 1}")

    def action_unhide_all_rows(self) -> None:
        """Ctrl+Shift+H -> make all hidden rows visible again"""
        if not self.hidden_rows:
            self._show_message("Info", "No hidden rows", "info")
            return
        self._push_undo()
        count = len(self.hidden_rows)
        self.hidden_rows.clear()
        self._finish_structural_change(f"Unhidden {count} row(s)")

    def action_hide_column(self) -> None:
        """Alt+H -> hide the currently focused column"""
        table   = self.query_one("#json-table", DataTable)
        col_idx = table.cursor_coordinate.column if table.cursor_coordinate else 0
        if col_idx == 0:
            self._show_message("Warning", "Cannot hide index column", "warning")
            return
        col_name = self.columns[col_idx]
        self._push_undo()
        self.hidden_columns.add(col_name)
        self._finish_structural_change(f"Hidden column '{col_name}'")

    def action_unhide_all_columns(self) -> None:
        """Alt+Shift+H -> reveal all hidden columns"""
        if not self.hidden_columns:
            self._show_message("Info", "No hidden columns", "info")
            return
        self._push_undo()
        count = len(self.hidden_columns)
        self.hidden_columns.clear()
        self._finish_structural_change(f"Unhidden {count} column(s)")

    # ================================================================== actions: resize

    def action_widen_column(self) -> None:
        """F2 -> increase the current column's display width"""
        col_name = self._current_col_name()
        if col_name is None:
            return
        current = self.column_widths.get(col_name, DEFAULT_COL_WIDTH)
        self.column_widths[col_name] = min(current + 4, MAX_COLUMN_WIDTH)
        self._populate_table()
        self._update_status(f"Column '{col_name}' width -> {self.column_widths[col_name]}")

    def action_narrow_column(self) -> None:
        """F3 -> decrease the current column's display width"""
        col_name = self._current_col_name()
        if col_name is None:
            return
        current = self.column_widths.get(col_name, DEFAULT_COL_WIDTH)
        self.column_widths[col_name] = max(current - 4, MIN_COLUMN_WIDTH)
        self._populate_table()
        self._update_status(f"Column '{col_name}' width -> {self.column_widths[col_name]}")

    def action_autofit_column(self) -> None:
        """Ctrl+Shift+F -> auto-fit column width to the longest value in that column"""
        col_name = self._current_col_name()
        if col_name is None:
            return
        max_len = len(col_name)
        for row in self.data:
            val = str(row.get(col_name, ""))
            if len(val) > max_len:
                max_len = len(val)
        new_width = min(max(max_len + 2, MIN_COLUMN_WIDTH), MAX_COLUMN_WIDTH)
        self.column_widths[col_name] = new_width
        self._populate_table()
        self._update_status(f"Auto-fit '{col_name}' -> {new_width}")

    def _current_col_name(self) -> Optional[str]:
        table   = self.query_one("#json-table", DataTable)
        col_idx = table.cursor_coordinate.column if table.cursor_coordinate else None
        if col_idx is None or col_idx >= len(self.columns):
            return None
        return self.columns[col_idx]

    # ================================================================== actions: sort

    def action_sort_asc(self) -> None:
        """F4 -> sort all rows ascending by the current column"""
        self._sort_by_column(reverse=False)

    def action_sort_desc(self) -> None:
        """F5 -> sort all rows descending by the current column"""
        self._sort_by_column(reverse=True)

    def _sort_by_column(self, reverse: bool) -> None:
        table   = self.query_one("#json-table", DataTable)
        col_idx = table.cursor_coordinate.column if table.cursor_coordinate else 1
        if col_idx == 0:
            self._show_message("Warning", "Cannot sort by index column", "warning")
            return
        col_name = self.columns[col_idx]
        self._push_undo()

        def sort_key(row: Dict) -> Any:
            val = row.get(col_name, "")
            # Try numeric sort first
            try:
                return (0, float(str(val)))
            except (ValueError, TypeError):
                return (1, str(val).lower())

        self.data.sort(key=sort_key, reverse=reverse)
        direction = "↓ Descending" if reverse else "↑ Ascending"
        self._finish_structural_change(f"Sorted '{col_name}' {direction}")

    # ================================================================== actions: find & replace

    def action_find_replace(self) -> None:
        """Ctrl+F -> open the find & replace dialog"""
        def on_result(result: Optional[Tuple[str, str]]) -> None:
            if result is None:
                return
            find_text, replace_text = result
            if not find_text:
                self._show_message("Find", "Search text is empty", "warning")
                return
            self._push_undo()
            count = 0
            for row in self.data:
                for col in self.columns[1:]:
                    if col in row:
                        old = str(row[col])
                        if find_text in old:
                            row[col] = old.replace(find_text, replace_text)
                            count += 1
            if count:
                self._finish_structural_change(f"Replaced {count} occurrence(s)")
            else:
                self._show_message("Find", f"'{find_text}' not found", "info")
                # Pop the undo we pushed prematurely
                self._undo_stack.pop()

        self.push_screen(FindReplaceScreen(), on_result)

    # ================================================================== actions: file

    def action_save(self) -> None:
        if not self.modified:
            self._show_message("Info", "No changes to save", "info")
            return
        try:
            with open(self.json_file, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
            self.modified = False
            self._update_save_status()
            self._update_status("File saved")
            self._show_message("Saved", f"Saved to:\n{self.json_file.name}", "success")
        except PermissionError:
            self._show_message("Error", "Permission denied", "error")
        except Exception as e:
            self._show_message("Error", f"Save failed:\n{str(e)[:40]}", "error")

    def action_reload(self) -> None:
        if self.modified:
            def on_confirm(confirmed: bool) -> None:
                if confirmed:
                    self.modified = False
                    self._update_save_status()
                    self.load_json()
            self.push_screen(ConfirmScreen("Reload File", "Discard changes?"), on_confirm)
        else:
            self.load_json()

    def action_deselect(self) -> None:
        self._update_status("Ready")

    def action_quit(self) -> None:
        if self.modified:
            def on_confirm(confirmed: bool) -> None:
                if confirmed:
                    self.exit()
            self.push_screen(ConfirmScreen("Quit", "Exit without saving?"), on_confirm)
        else:
            self.exit()

    #  data loading

    def load_json(self) -> None:
        try:
            suffix = self.json_file.suffix.lower()
            if suffix == ".json":
                with open(self.json_file, "r", encoding="utf-8") as f:
                    content = self._fix_json(f.read())
                self.data = json.loads(content)
                if not isinstance(self.data, list):
                    self.data = [self.data]
            elif suffix == ".csv":
                with open(self.json_file, "r", encoding="utf-8", newline="") as f:
                    self.data = [dict(row) for row in csv.DictReader(f)]
            else:
                raise ValueError(f"Unsupported file type: {suffix}")

            # Reset view state on fresh load
            self.hidden_rows.clear()
            self.hidden_columns.clear()
            self._undo_stack.clear()
            self._redo_stack.clear()
            self._populate_table()
            self._update_status(f"Loaded {len(self.data)} entries")
            self.modified = False
            self._update_save_status()
            self._last_mtime = os.path.getmtime(self.json_file)

        except FileNotFoundError:
            self._show_message("Error", f"File not found:\n{self.json_file}", "error")
        except json.JSONDecodeError as e:
            self._show_message("JSON Error", f"Invalid JSON:\n{str(e)[:40]}", "error")
        except Exception as e:
            self._show_message("Error", str(e)[:60], "error")

    def _reload_file(self) -> None:
        now = datetime.now().strftime("%H:%M:%S")
        self.load_json()
        self.notify(f"🔄 File reloaded at {now}", severity="information")

    def _poll_file_changes(self) -> None:
        if not self.json_file or not os.path.exists(self.json_file):
            return
        current_mtime = os.path.getmtime(self.json_file)
        if self._last_mtime is not None and current_mtime != self._last_mtime:
            self._last_mtime = current_mtime
            self._reload_file()

    def _fix_json(self, content: str) -> str:
        content = re.sub(r',\s*]', ']', content)
        content = re.sub(r',\s*}', '}', content)
        content = re.sub(r'(\{|,)\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*:', r'\1"\2":', content)
        return content

    # ================================================================== table population

    def _populate_table(self) -> None:
        """
        Rebuild the DataTable from self.data, respecting hidden rows/columns,
        column width overrides, and all formatting rules from TableFormattingConfig.
        """
        table = self.query_one("#json-table", DataTable)
        table.clear(columns=True)

        if not self.data:
            self._update_status("No data to display")
            return

        # ── Build ordered column list (unchanged) ────────────────────────────────
        if not self.columns:
            self.columns = ["entry"]
            for item in self.data:
                if isinstance(item, dict):
                    for key in item.keys():
                        if key not in self.columns:
                            self.columns.append(key)

        # ── Merge hidden columns: your app state + config ────────────────────────
        cfg_hidden   = {k for k, v in self._fmt_cfg.columns.items() if v.hidden}
        all_hidden   = self.hidden_columns | cfg_hidden

        visible_cols = [
            c for c in self.columns
            if c not in all_hidden or c == "entry"
        ]

        # ── Add columns (unchanged logic, now also reads config width/label) ─────
        for col in visible_cols:
            if col in all_hidden:
                continue
            col_cfg = self._fmt_cfg.columns.get(col)
            label   = col_cfg.label if col_cfg and col_cfg.label else col.upper()
            width   = self.column_widths.get(col) or (col_cfg.width if col_cfg else None)
            if width:
                table.add_column(label, key=col, width=width)
            else:
                table.add_column(label, key=col)

        # Pre-sort rules once per render, not once per cell
        sorted_rules = sorted(self._fmt_cfg.rules, key=lambda r: r.priority)

        # ── Add rows ─────────────────────────────────────────────────────────────
        for idx, item in enumerate(self.data):
            if idx in self.hidden_rows:
                continue
            if idx in self._fmt_cfg.hidden_row_indices:
                continue

            row_dict = item if isinstance(item, dict) else {}

            # Optional callable row filter from config
            if self._fmt_cfg.row_filter:
                if not self._fmt_cfg.row_filter(idx, row_dict, self.data):
                    continue

            display_idx = idx + 1

            # Zebra striping
            stripe = (
                self._fmt_cfg.stripe_even if display_idx % 2 == 0 and self._fmt_cfg.stripe_even else
                self._fmt_cfg.stripe_odd  if display_idx % 2 != 0 and self._fmt_cfg.stripe_odd  else
                ""
            )

            row_data = [Text(str(display_idx), style=f"#888888 {stripe}".strip())]

            if isinstance(item, dict):
                for col in visible_cols[1:]:    # skip "entry"
                    raw   = item.get(col, "")
                    start = str(raw) if raw is not None else ""

                    # Always-on column default_fmt (e.g. DIV always cyan)
                    col_cfg = self._fmt_cfg.columns.get(col)
                    if col_cfg and col_cfg.default_fmt:
                        seed_ctx = RuleContext(
                            row=row_dict, col=col, cell=raw, display=start,
                            idx=idx, display_idx=display_idx,
                            all_data=self.data, col_keys=visible_cols,
                        )
                        try:
                            start = col_cfg.default_fmt(seed_ctx)
                        except Exception:
                            pass

                    # ── Run the rule engine ──────────────────────────────────────
                    final = apply_rules(
                        rules       = sorted_rules,
                        row         = row_dict,
                        col         = col,
                        cell        = raw,
                        idx         = idx,
                        display_idx = display_idx,
                        all_data    = self.data,
                        col_keys    = visible_cols,
                    )

                    # Use rule output when it differs from the raw value
                    display_str = final if final != str(raw if raw is not None else "") else start

                    # Attach zebra stripe only if no explicit background was set by a rule
                    if stripe and "on " not in display_str:
                        display_str = f"[{stripe}]{display_str}[/{stripe}]"

                    row_data.append(Text.from_markup(display_str))
            else:
                row_data.append(str(item))
                row_data.extend([""] * (len(visible_cols) - 2))

            table.add_row(*row_data, key=str(display_idx))

        table.focus()
        table.refresh()   # ← redraws the widget after programmatic clear+fill
        self.refresh()

    # ================================================================== helpers

    def _finish_structural_change(self, status_msg: str) -> None:
        """Common tail for any operation that changes data shape"""
        self.modified = True
        self._update_save_status()
        self._populate_table()
        self._update_status(status_msg)

    def _update_save_status(self) -> None:
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
        self.push_screen(MessageBox(title, message, msg_type))

    def _update_status(self, message: str) -> None:
        status = self.query_one("#status-message", Static)
        cell_info = ""
        try:
            table = self.query_one("#json-table", DataTable)
            if table.cursor_coordinate:
                row      = table.cursor_coordinate.row + 1
                col      = table.cursor_coordinate.column + 1
                col_name = (
                    self.columns[table.cursor_coordinate.column]
                    if table.cursor_coordinate.column < len(self.columns) else ""
                )
                hidden_r = len(self.hidden_rows)
                hidden_c = len(self.hidden_columns)
                extras   = []
                if hidden_r:
                    extras.append(f"{hidden_r} row(s) hidden")
                if hidden_c:
                    extras.append(f"{hidden_c} col(s) hidden")
                extra_str = f"  [{', '.join(extras)}]" if extras else ""
                cell_info = f" │ R{row}C{col} ({col_name}){extra_str}"
        except Exception:
            pass
        status.update(f"{message}{cell_info}")

    def on_data_table_cell_highlighted(self, event: DataTable.CellHighlighted) -> None:
        self._update_status(f"Value: {event.value}")


# ──────────────────────────────────────────────────────────────────────────────
# Entry point helpers
# ──────────────────────────────────────────────────────────────────────────────

def create_sample_json(filename: str) -> None:
    sample_data = [
        {"date": "5/4/26", "nominal": "25",  "description": "Initial deposit"},
        {"date": "5/5/26", "nominal": "50",  "description": "Second payment"},
        {"date": "5/6/26", "nominal": "100", "description": "Third payment"},
        {"date": "5/7/26", "nominal": "75",  "description": "Fourth payment"},
        {"date": "5/8/26", "nominal": "200", "description": "Final payment"},
    ]
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(sample_data, f, indent=2)
    print(f"Created sample file: {filename}")


if __name__ == "__main__":
    import sys
    file = sys.argv[1] if len(sys.argv) > 1 else "sample.json"
    if not Path(file).exists():
        create_sample_json(file)
    JsonTableApp(file).run()
