"""
Minimalistic DropBox component for Textual.
"""

from __future__ import annotations

from textual import on
from textual.app import App, ComposeResult
from textual.containers import Vertical, Horizontal
from textual.css.query import NoMatches
from textual.message import Message
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Checkbox, Static
from textual.theme import Theme

class DropBox(Widget):
    """A minimal dropdown checkbox component."""

    DEFAULT_CSS = """
    DropBox {
        height: 1;
        width: auto;
    }

    DropBox > .dd-toggle {
        height: 1;
        width: auto;
        padding: 0;
        margin: 0;
        background: $primary;
        color: $text;
    }

    DropBox > .dd-toggle:hover {
        background: $primary-lighten-1;
    }

    DropBox > .dd-toggle:focus {
        text-style: reverse;
    }

    DropBox > .dd-panel {
        display: none;
        overlay: screen;
        layer: above;
        offset-y: 1;
        height: auto;
        max-height: 10;
        width: auto;
        overflow-y: auto;
        background: $surface;
        border: solid $primary;
    }

    DropBox > .dd-panel.open {
        display: block;
    }

    DropBox > .dd-panel .dd-item {
        height: 1;
        width: auto;
        min-width: 100%;
        padding: 0 1 0 0;
        margin: 0;
        border: none;
        background: transparent;
    }

    DropBox > .dd-panel .dd-item:hover {
        background: $primary 20%;
    }

    DropBox > .dd-panel .dd-item:focus {
        background: $primary 30%;
    }

    DropBox > .dd-panel .dd-actions {
        height: 1;
        width: 100%;
        padding: 0;
        margin: 0;
        layout: horizontal;
    }

    DropBox > .dd-panel .dd-action {
        height: 1;
        width: auto;
        padding: 0;
        margin: 0;
        background: $surface-lighten-1;
        color: $text-muted;
    }

    DropBox > .dd-panel .dd-action:hover {
        background: $primary 30%;
        color: $text;
    }
    """

    is_open: reactive[bool] = reactive(False)

    class Changed(Message):
        """Posted when selection changes."""

        def __init__(
            self,
            dropdown: DropBox,
            option: str,
            value: bool,
            selected: list[str],
        ) -> None:
            super().__init__()
            self.dropdown = dropdown
            self.option = option
            self.value = value
            self.selected = selected

        @property
        def control(self) -> DropBox:
            return self.dropdown

    def __init__(
        self,
        label: str = "Select",
        options: list[str] | None = None,
        selected: list[str] | None = None,
        show_count: bool = True,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        super().__init__(name=name, id=id, classes=classes)
        self._label = label
        self._options: list[str] = options or []
        self._pre_selected: set[str] = set(selected or [])
        self._show_count = show_count

    def compose(self) -> ComposeResult:
        yield Static(self._make_label(), classes="dd-toggle")
        with Vertical(classes="dd-panel"):
            with Horizontal(classes="dd-actions"):
                yield Static("All", classes="dd-action dd-all")
                yield Static("None", classes="dd-action dd-none")
            if self._options:
                for opt in self._options:
                    yield Checkbox(opt, opt in self._pre_selected, classes="dd-item")
            else:
                yield Static("(empty)", classes="dd-empty")

    @property
    def selected(self) -> list[str]:
        return [str(cb.label) for cb in self.query(".dd-item") if cb.value]

    @property
    def options(self) -> list[str]:
        return list(self._options)

    def set_options(self, options: list[str], selected: list[str] | None = None) -> None:
        self._options = list(options)
        self._pre_selected = set(selected or [])
        panel = self.query_one(".dd-panel", Vertical)
        for cb in list(panel.query(".dd-item")):
            cb.remove()
        try:
            panel.query_one(".dd-empty").remove()
        except NoMatches:
            pass
        if self._options:
            for opt in self._options:
                panel.mount(Checkbox(opt, opt in self._pre_selected, classes="dd-item"))
        else:
            panel.mount(Static("(empty)", classes="dd-empty"))
        self._refresh_label()

    def select_all(self) -> None:
        for cb in self.query(".dd-item"):
            cb.value = True
        self._refresh_label()

    def select_none(self) -> None:
        for cb in self.query(".dd-item"):
            cb.value = False
        self._refresh_label()

    def _make_label(self) -> str:
        arrow = "▲" if self.is_open else "▼"
        if self._show_count:
            n = len(self.selected) if self.is_mounted else len(self._pre_selected)
            return f"{self._label} ({n}) {arrow}"
        return f"{self._label}{arrow}"

    def _refresh_label(self) -> None:
        try:
            self.query_one(".dd-toggle", Static).update(self._make_label())
        except NoMatches:
            pass

    def watch_is_open(self, value: bool) -> None:
        try:
            self.query_one(".dd-panel").set_class(value, "open")
            self._refresh_label()
        except NoMatches:
            pass

    def on_click(self, event) -> None:
        """Handle clicks on toggle and action buttons."""
        try:
            toggle = self.query_one(".dd-toggle")
            if toggle.region.contains(event.screen_x, event.screen_y):
                self.is_open = not self.is_open
                return
        except NoMatches:
            pass

        try:
            all_btn = self.query_one(".dd-all")
            if all_btn.region.contains(event.screen_x, event.screen_y):
                self.select_all()
                return
        except NoMatches:
            pass

        try:
            none_btn = self.query_one(".dd-none")
            if none_btn.region.contains(event.screen_x, event.screen_y):
                self.select_none()
                return
        except NoMatches:
            pass

    @on(Checkbox.Changed, ".dd-item")
    def _on_checkbox_changed(self, event: Checkbox.Changed) -> None:
        event.stop()
        self._refresh_label()
        self.post_message(
            self.Changed(
                dropdown=self,
                option=str(event.checkbox.label),
                value=event.value,
                selected=self.selected,
            )
        )


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
        yield DropBox(
            label="Fruits",
            options=["Apple", "Banana", "Cherry", "Date", "Fig", "Grape"],
            selected=["Apple"],
            id="fruits",
        )
        yield Static("", id="output")

    @on(DropBox.Changed)
    def _changed(self, event: DropBox.Changed) -> None:
        sel = ", ".join(event.selected) or "none"
        self.query_one("#output", Static).update(f"Selected: {sel}")


if __name__ == "__main__":
    DemoApp().run()
