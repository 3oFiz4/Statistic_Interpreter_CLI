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
class AddColumnScreen(Screen):
    """Special dialog for entering a new column name"""

    DEFAULT_CSS = """
    AddColumnScreen { align: center middle; }
    #dialog {
        background: $surface; border: thick $accent;
        padding: 1 2; width: 50; height: auto;
    }
    #buttons { height: auto; }
    """

    def compose(self) -> ComposeResult:
        with Container(id="dialog"):
            yield Label("New column name:", id="label")
            yield Input(placeholder="column_name", id="col-input")
            with Horizontal(id="buttons"):
                yield Button("Add",    variant="primary", id="add")
                yield Button("Cancel", variant="default", id="cancel")

    def on_mount(self) -> None:
        self.query_one("#col-input", Input).focus()

    @on(Button.Pressed, "#add")
    def _add(self) -> None:
        self.dismiss(self.query_one("#col-input", Input).value.strip())

    @on(Button.Pressed, "#cancel")
    def _cancel(self) -> None: self.dismiss(None)

    def on_key(self, event) -> None:
        if event.key == "escape":
            self.dismiss(None)
        elif event.key == "enter":
            self.dismiss(self.query_one("#col-input", Input).value.strip())
