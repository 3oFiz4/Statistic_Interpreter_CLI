"""
Minimalistic InputBox component for Textual.

- Reusable component (Widget)
- Reactive value updates on every change (no Enter required)
- Posts InputBox.Changed message whenever the text changes
"""

from __future__ import annotations

from textual import on
from textual.app import App, ComposeResult
from textual.css.query import NoMatches
from textual.message import Message
from textual.reactive import reactive
from textual.widget import Widget
from textual.containers import Horizontal
from textual.widgets import Input, Static


class InputBox(Widget):
    """A minimal, reactive input component."""

    DEFAULT_CSS = """
InputBox {
        height: 1;
        width: auto;
    }

    InputBox > .in-row {
        height: 1;
        width: auto;
        padding: 0;
        margin: 0;
        layout: horizontal;
    }

    InputBox > .in-row > .in-label {
        height: 1;
        width: auto;
        padding: 0 1;
        margin: 0;
        background: $primary;
        color: $text;
    }

    InputBox > .in-row > .in-label:hover {
        background: $primary-lighten-1;
    }

    InputBox > .in-row > .in-label:focus {
        text-style: reverse;
    }

    /* NOTE:
       To be truly height: 1, the input must not have a border.
       A border would add 2 rows (top+bottom), forcing height >= 3.
    */
    InputBox > .in-row > .in-field {
        height: 1;
        width: 1fr;
        padding: 0 1;
        margin: 0;

        border: none;
        background: $surface;
        color: $text;
    }

    InputBox > .in-row > .in-field:focus {
        background: $primary 20%;
    }
    """

    value: reactive[str] = reactive("")

    class Changed(Message):
        """Posted whenever the input text changes (per keystroke)."""

        def __init__(self, input_box: InputBox, value: str) -> None:
            super().__init__()
            self.input_box = input_box
            self.value = value

        @property
        def control(self) -> InputBox:
            return self.input_box

    def __init__(
        self,
        label: str | None = None,
        value: str = "",
        placeholder: str = "",
        password: bool = False,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        super().__init__(name=name, id=id, classes=classes)
        self._label = label
        self._initial_value = value
        self._placeholder = placeholder
        self._password = password
        self._syncing = False

        # initialize reactive value
        self.value = value

    def compose(self) -> ComposeResult:
        with Horizontal(classes="in-row"):
            if self._label:
                yield Static(self._label, classes="in-label")
            yield Input(
                value=self._initial_value,
                placeholder=self._placeholder,
                password=self._password,
                classes="in-field",
            )

    def set_value(self, value: str) -> None:
        """Programmatically set the value (updates the Input widget too)."""
        self.value = value  # watch_value will sync the widget

    def watch_value(self, value: str) -> None:
        """Keep the Input widget in sync if value changes programmatically."""
        if self._syncing:
            return
        try:
            inp = self.query_one(".in-field", Input)
        except NoMatches:
            return
        if inp.value != value:
            self._syncing = True
            try:
                inp.value = value
            finally:
                self._syncing = False

    @on(Input.Changed, ".in-field")
    def _on_input_changed(self, event: Input.Changed) -> None:
        """Update reactive value on every keystroke and post Changed."""
        event.stop()
        if self._syncing:
            return
        self._syncing = True
        try:
            self.value = event.value
        finally:
            self._syncing = False

        self.post_message(self.Changed(self, event.value))


# ─────────────────────────────────────────────────────────────
# Demo
# ─────────────────────────────────────────────────────────────

class DemoApp(App):
    CSS = """
    Screen {
        padding: 1;
    }

    #output {
        height: 1;
        margin-top: 1;
        color: $text-muted;
    }
    """

    def compose(self) -> ComposeResult:
        yield InputBox(label="Name", placeholder="type here...", id="name")
        yield Static("", id="output")

    @on(InputBox.Changed)
    def _changed(self, event: InputBox.Changed) -> None:
        self.query_one("#output", Static).update(f"Value: {event.value!r}")


if __name__ == "__main__":
    DemoApp().run()
