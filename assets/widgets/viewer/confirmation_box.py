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
# those imports are template, its that i assume they are often goes in those import patterns.
# 
class ConfirmScreen(Screen):
    """Yes/No check modal"""

    DEFAULT_CSS = """
    ConfirmScreen { align: center middle; }
    #dialog {
        background: $surface; border: thick $warning;
        padding: 1 2; width: 50; height: auto;
    }
    #dialog-title { text-style: bold; color: $warning; margin-bottom: 1; }
    #dialog-msg   { margin-bottom: 1; }
    #buttons      { height: auto; }
    """

    def __init__(self, title: str, message: str) -> None:
        super().__init__()
        self._title   = title
        self._message = message

    def compose(self) -> ComposeResult:
        with Container(id="dialog"):
            yield Label(self._title,   id="dialog-title")
            yield Label(self._message, id="dialog-msg")
            with Horizontal(id="buttons"):
                yield Button("Yes", variant="error",   id="yes")
                yield Button("No",  variant="primary", id="no")

    @on(Button.Pressed, "#yes")
    def _yes(self) -> None: self.dismiss(True)

    @on(Button.Pressed, "#no")
    def _no(self)  -> None: self.dismiss(False)

    def on_key(self, event) -> None:
        if event.key == "escape":
            self.dismiss(False)
        elif event.key == "enter":
            self.dismiss(True)
