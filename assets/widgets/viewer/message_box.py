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
# Dialog screens
class MessageBox(Screen):
    """MsgBox process, shows a title + message with an OK button."""
    DEFAULT_CSS = """
    MessageBox {
        align: center middle;
    }
    #dialog {
        background: $surface;
        border: thick $primary;
        padding: 1 2;
        width: 50;
        height: auto;
    }
    #dialog-title { text-style: bold; color: $primary; margin-bottom: 1; }
    #dialog-msg   { margin-bottom: 1; }
    """
    def __init__(self, title: str, message: str, msg_type: str = "info") -> None:
        super().__init__()
        self._title   = title
        self._message = message
        self._type    = msg_type

    def compose(self) -> ComposeResult:
        with Container(id="dialog"):
            yield Label(self._title,   id="dialog-title")
            yield Label(self._message, id="dialog-msg")
            yield Button("OK", variant="primary", id="ok")

    @on(Button.Pressed, "#ok")
    def _ok(self) -> None:
        self.dismiss()

    def on_key(self, event) -> None:
        if event.key in ("enter", "escape"):
            self.dismiss()
