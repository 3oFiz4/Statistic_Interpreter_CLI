"""
DropBox widget implementation for Textual.

This module provides a compact, reusable dropdown component that
presents a list of options as checkboxes.  Users can toggle the
dropdown open/closed, select or deselect individual items, or use the
“All” / “None” actions to modify the entire selection at once.

The widget emits a ``DropBox.Changed`` message whenever the selection
changes, allowing parent widgets or applications to react
reactively.  A small demo application is included at the bottom of the
file to illustrate typical usage.
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
    """A minimal dropdown checkbox component.

    The widget consists of a toggle line (showing the label, an optional
    count of selected items, and an arrow indicating open/closed state)
    and a panel that contains:
      * “All” and “None” action buttons.
      * A vertical list of ``Checkbox`` widgets, one per option.

    Selection changes are emitted via the nested ``Changed`` message,
    which carries the option that changed, its new boolean value, and
    the full list of currently selected options.
    """

    # --------------------------------------------------------------------- #
    # Default CSS styling for the widget
    # --------------------------------------------------------------------- #
    DEFAULT_CSS = """
    /* The outer DropBox container – height of a single line. */
    DropBox {
        height: 1;
        width: auto;
    }

    /* The clickable toggle line. */
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

    /* The dropdown panel – hidden by default, shown when .open class is set. */
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

    /* Individual checkbox items inside the panel. */
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

    /* Container for the “All” / “None” action buttons. */
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

    # --------------------------------------------------------------------- #
    # Reactive state: whether the dropdown panel is currently open.
    # --------------------------------------------------------------------- #
    is_open: reactive[bool] = reactive(False)

    # --------------------------------------------------------------------- #
    # Message class emitted when the selection changes.
    # --------------------------------------------------------------------- #
    class Changed(Message):
        """Message posted by ``DropBox`` when a checkbox value changes."""

        def __init__(
            self,
            dropdown: "DropBox",
            option: str,
            value: bool,
            selected: list[str],
        ) -> None:
            """Create a ``Changed`` message.

            Parameters
            ----------
            dropdown: DropBox
                The widget instance that generated the event.
            option: str
                The label of the checkbox that changed.
            value: bool
                The new checked state of that checkbox.
            selected: list[str]
                The full list of currently selected option labels.
            """
            super().__init__()
            self.dropdown = dropdown
            self.option = option
            self.value = value
            self.selected = selected

        @property
        def control(self) -> "DropBox":
            """Alias used by Textual for ``event.control``."""
            return self.dropdown

    # --------------------------------------------------------------------- #
    # Construction
    # --------------------------------------------------------------------- #
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
        """Initialize the DropBox widget.

        Parameters
        ----------
        label: str
            Text displayed on the toggle line.
        options: list[str] | None
            List of option strings; each becomes a ``Checkbox``.
        selected: list[str] | None
            Options that should start checked.
        show_count: bool
            If ``True`` the toggle shows ``(n)`` where *n* is the number of
            selected items.
        name, id, classes: optional widget identifiers.
        """
        super().__init__(name=name, id=id, classes=classes)
        self._label = label
        self._options: list[str] = options or []
        self._pre_selected: set[str] = set(selected or [])
        self._show_count = show_count

    # --------------------------------------------------------------------- #
    # UI composition – builds the widget hierarchy.
    # --------------------------------------------------------------------- #
    def compose(self) -> ComposeResult:
        """Create the child widgets for the dropdown.

        The toggle line is a ``Static`` widget; the panel is a ``Vertical``
        container that holds the action buttons and the option checkboxes.
        """
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

    # --------------------------------------------------------------------- #
    # Public read‑only properties
    # --------------------------------------------------------------------- #
    @property
    def selected(self) -> list[str]:
        """Return a list of labels for checkboxes that are currently checked."""
        return [str(cb.label) for cb in self.query(".dd-item") if cb.value]

    @property
    def options(self) -> list[str]:
        """Return the full list of option strings."""
        return list(self._options)

    # --------------------------------------------------------------------- #
    # Public API for dynamically updating the options list.
    # --------------------------------------------------------------------- #
    def set_options(
        self, options: list[str], selected: list[str] | None = None
    ) -> None:
        """Replace the option list and optionally set a new selection.

        The panel is cleared and rebuilt with fresh ``Checkbox`` widgets.
        """
        self._options = list(options)
        self._pre_selected = set(selected or [])
        panel = self.query_one(".dd-panel", Vertical)

        # Remove any existing option checkboxes.
        for cb in list(panel.query(".dd-item")):
            cb.remove()

        # Remove the empty placeholder if present.
        try:
            panel.query_one(".dd-empty").remove()
        except NoMatches:
            pass

        # Populate new options or show empty placeholder.
        if self._options:
            for opt in self._options:
                panel.mount(Checkbox(opt, opt in self._pre_selected, classes="dd-item"))
        else:
            panel.mount(Static("(empty)", classes="dd-empty"))

        self._refresh_label()

    def select_all(self) -> None:
        """Mark every option as selected."""
        for cb in self.query(".dd-item"):
            cb.value = True
        self._refresh_label()

    def select_none(self) -> None:
        """Clear all selections."""
        for cb in self.query(".dd-item"):
            cb.value = False
        self._refresh_label()

    # --------------------------------------------------------------------- #
    # Helper methods for rendering the toggle label.
    # --------------------------------------------------------------------- #
    def _make_label(self) -> str:
        """Construct the toggle label string.

        Includes the arrow indicating open/closed state and, if enabled,
        the count of selected items.
        """
        arrow = "▲" if self.is_open else "▼"
        if self._show_count:
            # ``is_mounted`` tells us whether the widget is already in the DOM.
            n = len(self.selected) if self.is_mounted else len(self._pre_selected)
            return f"{self._label} ({n}) {arrow}"
        return f"{self._label}{arrow}"

    def _refresh_label(self) -> None:
        """Update the ``.dd-toggle`` widget with the latest label text."""
        try:
            self.query_one(".dd-toggle", Static).update(self._make_label())
        except NoMatches:
            pass

    # --------------------------------------------------------------------- #
    # Reactive watch – called automatically when ``is_open`` changes.
    # --------------------------------------------------------------------- #
    def watch_is_open(self, value: bool) -> None:
        """Show or hide the dropdown panel based on ``is_open``."""
        try:
            self.query_one(".dd-panel").set_class(value, "open")
            self._refresh_label()
        except NoMatches:
            pass

    # --------------------------------------------------------------------- #
    # Event handling – mouse clicks on the toggle line and action buttons.
    # --------------------------------------------------------------------- #
    def on_click(self, event) -> None:
        """Handle clicks on the toggle line, “All”, and “None” buttons."""
        # Toggle line – open/close the panel.
        try:
            toggle = self.query_one(".dd-toggle")
            if toggle.region.contains(event.screen_x, event.screen_y):
                self.is_open = not self.is_open
                return
        except NoMatches:
            pass

        # “All” action – select every option.
        try:
            all_btn = self.query_one(".dd-all")
            if all_btn.region.contains(event.screen_x, event.screen_y):
                self.select_all()
                return
        except NoMatches:
            pass

        # “None” action – clear all selections.
        try:
            none_btn = self.query_one(".dd-none")
            if none_btn.region.contains(event.screen_x, event.screen_y):
                self.select_none()
                return
        except NoMatches:
            pass

    # --------------------------------------------------------------------- #
    # Checkbox change handler – reacts to individual checkbox toggles.
    # --------------------------------------------------------------------- #
    @on(Checkbox.Changed, ".dd-item")
    def _on_checkbox_changed(self, event: Checkbox.Changed) -> None:
        """Emit a ``DropBox.Changed`` message when a checkbox changes."""
        event.stop()  # Prevent further propagation.
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
# Demo application – shows the DropBox in a minimal Textual app.
# ─────────────────────────────────────────────────────────────
class DemoApp(App):
    """Simple demo showing the DropBox widget in action."""

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
        """Create a DropBox and an output area for displaying selections."""
        yield DropBox(
            label="Fruits",
            options=["Apple", "Banana", "Cherry", "Date", "Fig", "Grape"],
            selected=["Apple"],
            id="fruits",
        )
        yield Static("", id="output")

    @on(DropBox.Changed)
    def _changed(self, event: DropBox.Changed) -> None:
        """Update the output area whenever the selection changes."""
        sel = ", ".join(event.selected) or "none"
        self.query_one("#output", Static).update(f"Selected: {sel}")


if __name__ == "__main__":
    DemoApp().run()
