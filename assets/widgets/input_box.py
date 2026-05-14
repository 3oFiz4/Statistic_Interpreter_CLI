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


# ----------------------------------------------------------------------
# InputBox widget
# ----------------------------------------------------------------------
# This widget combines an optional label with a Textual ``Input`` field.
# It maintains a reactive ``value`` attribute that mirrors the content
# of the underlying ``Input`` widget.  Whenever the user types, the
# widget updates ``value`` and emits a custom ``Changed`` message so
# that parent components can react instantly (per keystroke, without
# waiting for the user to press Enter).  The widget also supports
# programmatic updates via ``set_value`` while keeping the UI in sync.
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

    # Reactive attribute that stores the current text value.
    value: reactive[str] = reactive("")

    # ------------------------------------------------------------------
    # Message class
    # ------------------------------------------------------------------
    # Emitted whenever the input text changes.  It carries a reference
    # to the originating ``InputBox`` instance and the new string value.
    class Changed(Message):
        """Posted whenever the input text changes (per keystroke)."""

        def __init__(self, input_box: InputBox, value: str) -> None:
            super().__init__()
            self.input_box = input_box
            self.value = value

        @property
        def control(self) -> InputBox:
            return self.input_box

    # ------------------------------------------------------------------
    # Constructor
    # ------------------------------------------------------------------
    # Parameters:
    #   label       – Optional static label displayed left of the field.
    #   value       – Initial text value.
    #   placeholder – Placeholder text shown when the field is empty.
    #   password    – If True, masks input (useful for passwords).
    #   name/id/classes – Standard widget identification arguments.
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

    # ------------------------------------------------------------------
    # Compose UI
    # ------------------------------------------------------------------
    # Builds a horizontal container with an optional label and the
    # Textual ``Input`` widget.  The ``Input`` receives the initial
    # value, placeholder, and password flag.
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

    # ------------------------------------------------------------------
    # Public API – set_value
    # ------------------------------------------------------------------
    # Allows external code to change the widget's value.  The reactive
    # ``value`` setter triggers ``watch_value`` which updates the UI.
    def set_value(self, value: str) -> None:
        """Programmatically set the value (updates the Input widget too)."""
        self.value = value  # watch_value will sync the widget

    # ------------------------------------------------------------------
    # Reactive watcher – watch_value
    # ------------------------------------------------------------------
    # Called automatically when ``self.value`` changes.  It ensures the
    # underlying ``Input`` widget reflects the new value, avoiding
    # infinite loops via the ``_syncing`` guard.
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

    # ------------------------------------------------------------------
    # Event handler – _on_input_changed
    # ------------------------------------------------------------------
    # Reacts to the ``Input.Changed`` event from the child ``Input``.
    # Updates the reactive ``value`` and posts the custom ``Changed``
    # message so external listeners can react instantly.
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
# Demo application
# ─────────────────────────────────────────────────────────────
# Shows the InputBox in action.  The demo updates a static text
# element with the current value each time the user types.
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
