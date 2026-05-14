"""
Minimalistic RadioGroup component for Textual.
"""

from __future__ import annotations

from textual import on
from textual.app import App, ComposeResult
from textual.containers import Vertical
from textual.css.query import NoMatches
from textual.message import Message
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import RadioButton, RadioSet, Static
from ..themes.crimson_demon import LoadTheme # temporary, delete when finish

class RadioGroup(Widget):
    """A configurable, reusable radio-button group component."""

    # ── CSS ──────────────────────────────────────────────────
    # Follows the same structural conventions as the reference
    # DropBox component: compact sizing, $primary/$surface
    # palette tokens, clear hover/focus feedback.
    # ─────────────────────────────────────────────────────────

    DEFAULT_CSS = """
    RadioGroup {
        height: auto;
        width: auto;
    }

    RadioGroup > .rg-header {
        height: 1;
        width: auto;
        padding: 0;
        margin: 0;
        background: $primary;
        color: $text;
    }

    RadioGroup > .rg-header:hover {
        background: $primary-lighten-1;
    }

    RadioGroup > .rg-header:focus {
        text-style: reverse;
    }

    RadioGroup > .rg-panel {
        height: auto;
        max-height: 12;
        width: auto;
        overflow-y: auto;
        background: $surface;
        border: solid $primary;
        padding: 0;
        margin: 0;
    }

    RadioGroup > .rg-panel RadioSet {
        height: auto;
        width: auto;
        min-width: 100%;
        padding: 0;
        margin: 0;
        background: transparent;
        border: none;
    }

    RadioGroup > .rg-panel RadioSet RadioButton {
        height: 1;
        width: auto;
        min-width: 100%;
        padding: 0 1 0 0;
        margin: 0;
        border: none;
        background: transparent;
    }

    RadioGroup > .rg-panel RadioSet RadioButton:hover {
        background: $primary 20%;
    }

    RadioGroup > .rg-panel RadioSet RadioButton:focus {
        background: $primary 30%;
    }

    RadioGroup > .rg-panel .rg-empty {
        height: 1;
        width: auto;
        padding: 0 1;
        margin: 0;
        color: $text-muted;
        background: transparent;
    }
    """

    # ── Reactive state ───────────────────────────────────────

    selected_index: reactive[int | None] = reactive[int | None](None)

    # ── Messages ─────────────────────────────────────────────

    class Changed(Message):
        """Posted when the selected radio button changes."""

        def __init__(
            self,
            radio_group: RadioGroup,
            value: str,
            index: int,
        ) -> None:
            super().__init__()
            self.radio_group = radio_group
            self.value = value
            self.index = index

        @property
        def control(self) -> RadioGroup:
            return self.radio_group

    # ── Constructor ──────────────────────────────────────────

    def __init__(
        self,
        label: str = "Choose",
        options: list[str] | None = None,
        default: str | None = None,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        super().__init__(name=name, id=id, classes=classes)
        self._label = label
        self._options: list[str] = list(options or [])
        self._default: str | None = default

    # ── Compose ──────────────────────────────────────────────

    def compose(self) -> ComposeResult:
        yield Static(self._make_header(), classes="rg-header")
        with Vertical(classes="rg-panel"):
            if self._options:
                with RadioSet(id="rg-radioset"):
                    for opt in self._options:
                        yield RadioButton(
                            opt,
                            value=(opt == self._default),
                        )
            else:
                yield Static("(no options)", classes="rg-empty")

    # ── Public properties ────────────────────────────────────

    @property
    def selected_value(self) -> str | None:
        """Return the label text of the currently-selected button."""
        try:
            rs = self.query_one("#rg-radioset", RadioSet)
            idx = rs.pressed_index
            if idx is not None and idx >= 0:
                btn: RadioButton = rs.children[idx]  # type: ignore[assignment]
                return str(btn.label)
        except NoMatches:
            pass
        return None

    @property
    def options(self) -> list[str]:
        """Return a copy of the current option list."""
        return list(self._options)

    # ── Public mutators ──────────────────────────────────────

    def set_options(
        self,
        options: list[str],
        default: str | None = None,
    ) -> None:
        """Replace every option at runtime."""
        self._options = list(options)
        self._default = default

        panel = self.query_one(".rg-panel", Vertical)

        # Remove old radio set or empty placeholder.
        try:
            panel.query_one("#rg-radioset").remove()
        except NoMatches:
            pass
        try:
            panel.query_one(".rg-empty").remove()
        except NoMatches:
            pass

        # Mount fresh widgets.
        if self._options:
            rs = RadioSet(id="rg-radioset")
            panel.mount(rs)
            for opt in self._options:
                rs.mount(RadioButton(opt, value=(opt == self._default)))
        else:
            panel.mount(Static("(no options)", classes="rg-empty"))

        self._refresh_header()

    def select_by_index(self, index: int) -> None:
        """Programmatically select a button by its zero-based index."""
        try:
            rs = self.query_one("#rg-radioset", RadioSet)
            buttons: list[RadioButton] = list(rs.query(RadioButton))
            if 0 <= index < len(buttons):
                buttons[index].value = True
                self._refresh_header()
        except NoMatches:
            pass

    def select_by_value(self, value: str) -> None:
        """Programmatically select a button whose label matches *value*."""
        try:
            rs = self.query_one("#rg-radioset", RadioSet)
            for btn in rs.query(RadioButton):
                if str(btn.label) == value:
                    btn.value = True
                    self._refresh_header()
                    return
        except NoMatches:
            pass

    # ── Internal helpers ─────────────────────────────────────

    def _make_header(self) -> str:
        sel = self.selected_value if self.is_mounted else (self._default or "—")
        return f"{self._label}: {sel or '—'}"

    def _refresh_header(self) -> None:
        try:
            self.query_one(".rg-header", Static).update(self._make_header())
        except NoMatches:
            pass

    # ── Event handling ───────────────────────────────────────

    @on(RadioSet.Changed, "#rg-radioset")
    def _on_radio_changed(self, event: RadioSet.Changed) -> None:
        event.stop()
        idx = event.radio_set.pressed_index
        value = str(event.pressed.label) if event.pressed else ""
        self.selected_index = idx
        self._refresh_header()
        self.post_message(
            self.Changed(
                radio_group=self,
                value=value,
                index=idx if idx is not None else -1,
            )
        )


# ─────────────────────────────────────────────────────────────
# Demo
# ─────────────────────────────────────────────────────────────


class DemoApp(App):
    """Tiny app that exercises the RadioGroup component."""

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
        yield RadioGroup(
            label="Colour",
            options=["Red", "Green", "Blue", "Yellow", "Cyan", "Magenta"],
            default="Blue",
            id="colours",
        )
        yield Static("", id="output")

    @on(RadioGroup.Changed)
    def _changed(self, event: RadioGroup.Changed) -> None:
        self.query_one("#output", Static).update(
            f"Selected: {event.value}  (index {event.index})"
        )


if __name__ == "__main__":
    DemoApp().run()
