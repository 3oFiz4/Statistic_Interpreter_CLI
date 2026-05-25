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

class FindReplaceScreen(Screen):
    """Find & replace dialog"""

    DEFAULT_CSS = """
    FindReplaceScreen { align: center middle; }
    #dialog {
        background: $surface; border: thick $accent;
        padding: 1 2; width: 60; height: auto;
    }
    Label     { margin-bottom: 0; }
    Input     { margin-bottom: 1; }
    #buttons  { height: auto; }
    """

    def compose(self) -> ComposeResult:
        with Container(id="dialog"):
            yield Label("Find & Replace", id="title")
            yield Label("Find:")
            yield Input(placeholder="search text", id="find-input")
            yield Label("Replace with:")
            yield Input(placeholder="replacement",  id="replace-input")
            with Horizontal(id="buttons"):
                yield Button("Replace All", variant="primary", id="replace")
                yield Button("Cancel",      variant="default", id="cancel")

    def on_mount(self) -> None:
        self.query_one("#find-input", Input).focus()

    @on(Button.Pressed, "#replace")
    def _replace(self) -> None:
        find    = self.query_one("#find-input",   Input).value
        replace = self.query_one("#replace-input", Input).value
        self.dismiss((find, replace))

    @on(Button.Pressed, "#cancel")
    def _cancel(self) -> None: self.dismiss(None)

    def on_key(self, event) -> None:
        if event.key == "escape":
            self.dismiss(None)
