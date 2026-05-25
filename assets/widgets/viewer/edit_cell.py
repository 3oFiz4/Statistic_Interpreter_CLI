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

class EditCellScreen(Screen):
    """One-single-field editor for sinlge cell value"""

    DEFAULT_CSS = """
    EditCellScreen { align: center middle; }
    #dialog {
        background: $surface; border: thick $accent;
        padding: 1 2; width: 60; height: auto;
    }
    #dialog-title { text-style: bold; margin-bottom: 1; }
    #edit-input   { margin-bottom: 1; }
    #buttons      { height: auto; }
    """

    def __init__(self, current_value: str, column_name: str) -> None:
        super().__init__()
        self._value  = current_value
        self._column = column_name

    def compose(self) -> ComposeResult:
        with Container(id="dialog"):
            yield Label(f"Edit: {self._column}", id="dialog-title")
            yield Input(value=self._value, id="edit-input")
            with Horizontal(id="buttons"):
                yield Button("Save",   variant="primary", id="save")
                yield Button("Cancel", variant="default", id="cancel")

    def on_mount(self) -> None:
        self.query_one("#edit-input", Input).focus()

    @on(Button.Pressed, "#save")
    def _save(self)   -> None:
        self.dismiss(self.query_one("#edit-input", Input).value)

    @on(Button.Pressed, "#cancel")
    def _cancel(self) -> None: self.dismiss(None)

    def on_key(self, event) -> None:
        if event.key == "escape":
            self.dismiss(None)
        elif event.key == "enter":
            self.dismiss(self.query_one("#edit-input", Input).value)
