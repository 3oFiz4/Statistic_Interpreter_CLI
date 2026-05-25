"""
Accordion widget module.

Provides a reusable accordion component with a header that toggles visibility
of its body. Includes lightweight custom input widgets (RadioGroup,
DropBox, InputBox) used in the demo application.

The implementation is deliberately simple and avoids external dependencies
beyond Textual.  All widgets are built from Textual's core primitives and
use reactive state to drive CSS class changes.
"""

from textual.app import App, ComposeResult
from textual.widgets import Static, Input, Checkbox, RadioButton, RadioSet, Label
from textual.containers import Vertical, Container
from textual.widget import Widget
from textual.events import Click
from textual.reactive import reactive


# ──────────────────────────────────────────────────────────────────────────────
# CUSTOM INPUT WIDGETS
# ──────────────────────────────────────────────────────────────────────────────


class RadioGroup(Container):
    """
    A labeled group of radio buttons where only one option can be selected.

    Parameters
    ----------
    label: str
        Text displayed above the radio set.
    options: list[str]
        List of option labels; each becomes a RadioButton.
    default: str | None
        The option that should be pre‑selected when the widget is created.
    **kwargs
        Additional arguments passed to the underlying Container.
    """

    DEFAULT_CSS = """
    RadioGroup {
        height: auto;
        margin: 1 0;
        padding: 0 1;
    }
    
    RadioGroup > Label {
        text-style: bold;
        color: $text;
        margin-bottom: 1;
    }
    
    RadioGroup RadioSet {
        height: auto;
        background: transparent;
    }
    """

    def __init__(
        self,
        label: str,
        options: list[str],
        default: str = None,
        **kwargs
    ) -> None:
        super().__init__(**kwargs)
        self._label = label          # Store the label text for later composition
        self._options = options      # Store the list of option strings
        self._default = default      # Store the default selection (may be None)

    def compose(self) -> ComposeResult:
        """Build the radio group structure."""
        # First render the label above the radio buttons
        yield Label(self._label)

        # RadioSet groups the RadioButton widgets; only one can be active
        with RadioSet():
            for option in self._options:
                # The default option receives ``value=True`` so it starts selected
                is_default = (option == self._default)
                yield RadioButton(option, value=is_default)


class DropBox(Container):
    """
    A multi‑select dropdown implemented with checkboxes.

    Parameters
    ----------
    label: str
        Text displayed above the list of checkboxes.
    options: list[str]
        All possible selectable items.
    selected: list[str] | None
        Items that should be pre‑checked when the widget is created.
    **kwargs
        Additional arguments passed to the underlying Container.
    """

    DEFAULT_CSS = """
    DropBox {
        height: auto;
        margin: 1 0;
        padding: 0 1;
    }
    
    DropBox > Label {
        text-style: bold;
        color: $text;
        margin-bottom: 1;
    }
    
    DropBox > Vertical {
        height: auto;
        padding-left: 2;
    }
    
    DropBox Checkbox {
        height: auto;
        padding: 0;
        margin: 0;
    }
    """

    def __init__(
        self,
        label: str,
        options: list[str],
        selected: list[str] = None,
        **kwargs
    ) -> None:
        super().__init__(**kwargs)
        self._label = label
        self._options = options
        # Normalise ``selected`` to an empty list if ``None`` was passed
        self._selected = selected or []

    def compose(self) -> ComposeResult:
        """Build the checkbox dropdown structure."""
        yield Label(self._label)

        # Use a Vertical container to stack the checkboxes
        with Vertical():
            for option in self._options:
                # Pre‑select any option that appears in ``self._selected``
                is_selected = option in self._selected
                yield Checkbox(option, value=is_selected)


class InputBox(Container):
    """
    A labeled text input field.

    Parameters
    ----------
    label: str
        Text displayed above the input widget.
    placeholder: str
        Placeholder text shown when the input is empty.
    **kwargs
        Additional arguments passed to the underlying Container.
    """

    DEFAULT_CSS = """
    InputBox {
        height: auto;
        margin: 1 0;
        padding: 0 1;
    }
    
    InputBox > Label {
        text-style: bold;
        color: $text;
        margin-bottom: 1;
    }
    
    InputBox Input {
        width: 100%;
    }
    """

    def __init__(
        self,
        label: str,
        placeholder: str = "",
        **kwargs
    ) -> None:
        super().__init__(**kwargs)
        self._label = label
        self._placeholder = placeholder

    def compose(self) -> ComposeResult:
        """Build the labeled input structure."""
        yield Label(self._label)
        yield Input(placeholder=self._placeholder)


# ──────────────────────────────────────────────────────────────────────────────
# ACCORDION WIDGET COMPONENTS
# ──────────────────────────────────────────────────────────────────────────────


class AccordionHeader(Static, can_focus=True):
    """
    The clickable header bar of the Accordion.

    The header displays a title centered within a line of ``|`` characters.
    It is focusable and reacts to hover/focus CSS selectors.
    """

    DEFAULT_CSS = """
    AccordionHeader {
        width: 100%;
        height: 1;
        background: $primary;
        color: $text;
        text-style: bold;
        content-align: center middle;
    }
    
    /* Visual feedback on hover */
    AccordionHeader:hover {
        background: $primary-darken-3;
    }
    
    /* Visual feedback when focused */
    AccordionHeader:focus {
        background: $primary;
    }
    """

    def __init__(self, title: str, **kwargs) -> None:
        super().__init__(**kwargs)
        self._title = title  # Store the raw title; rendering adds padding/fill

    def on_mount(self) -> None:
        """Initial rendering of the title when the widget is first added."""
        self._render_title()

    def on_resize(self) -> None:
        """Re‑render the title whenever the widget's width changes."""
        self._render_title()

    def _render_title(self) -> None:
        """
        Render the accordion title with a ``|`` background pattern.

        The title is padded with a single space on each side, then the
        remaining width is split evenly between left and right fill characters.
        This ensures the title stays centered even when the container is resized.
        """
        width = self.size.width

        # Guard against zero or negative width (can happen during early layout)
        if width <= 0:
            return

        # Add spaces around the title for visual separation
        title_with_padding = f" {self._title} "
        title_length = len(title_with_padding)

        # Compute how many fill characters are needed on each side
        remaining_space = max(0, width - title_length)
        left_fill = remaining_space // 2          # Left side fill count
        right_fill = remaining_space - left_fill  # Right side (handles odd widths)

        # Build the final display string: "||| Title |||"
        display_text = ("|" * left_fill) + title_with_padding + ("|" * right_fill)

        # Update the widget's content
        self.update(display_text)


class AccordionBody(Container):
    """
    The content container of the Accordion.

    Items remain mounted in the DOM even when hidden; visibility is controlled
    via CSS ``display`` property toggled by the ``-expanded`` class on the
    parent ``Accordion``.
    """

    DEFAULT_CSS = """
    AccordionBody {
        width: 100%;
        height: auto;
        background: $surface;
        /* Hidden by default - items stay in DOM */
        display: none;
    }
    """


class Accordion(Container):
    """
    A custom Accordion widget that expands/collapses on click.

    Two ways to add content:

    1. ``with`` syntax (recommended for readability):
       ```python
       with Accordion("Title"):
           yield WidgetA()
           yield WidgetB()
       ```

    2. Constructor arguments:
       ```python
       Accordion("Title", WidgetA(), WidgetB())
       ```

    The widget uses a reactive ``expanded`` flag to toggle a CSS class,
    which in turn shows or hides the ``AccordionBody``.
    """

    expanded: reactive[bool] = reactive(False)

    DEFAULT_CSS = """
    Accordion {
        width: 100%;
        height: auto;
        margin: 1 0;
    }
    
    Accordion.-expanded AccordionBody {
        display: block;
    }
    """

    def __init__(self, title: str, *children: Widget, **kwargs) -> None:
        super().__init__(**kwargs)
        self._title = title
        # Store children passed via constructor OR collected via ``with`` syntax
        self._accordion_children: list[Widget] = list(children)
        # Reference to the body container (populated in ``compose``)
        self._body: AccordionBody | None = None

    def compose(self) -> ComposeResult:
        """Compose the static header and the body container."""
        yield AccordionHeader(self._title)
        self._body = AccordionBody()
        yield self._body

    def compose_add_child(self, widget: Widget) -> None:
        """
        Called automatically for each widget yielded inside a ``with Accordion():``
        block.  The widget is stored temporarily and later mounted into the body.
        """
        self._accordion_children.append(widget)

    def on_mount(self) -> None:
        """After the Accordion is mounted, move all collected children into the body."""
        if self._body and self._accordion_children:
            for child in self._accordion_children:
                self._body.mount(child)
            # Clear the temporary list – children are now part of the body
            self._accordion_children.clear()

    def watch_expanded(self, expanded: bool) -> None:
        """React to changes in ``expanded`` by adding or removing the ``-expanded`` CSS class."""
        self.set_class(expanded, "-expanded")

    def on_click(self, event: Click) -> None:
        """Toggle the accordion only when the header is clicked."""
        if isinstance(event.control, AccordionHeader):
            self.expanded = not self.expanded


# ──────────────────────────────────────────────────────────────────────────────
# MAIN APPLICATION
# ──────────────────────────────────────────────────────────────────────────────


class AccordionDemoApp(App):
    """Demo application showcasing the Accordion with custom input widgets."""

    CSS = """
    Screen {
        background: $background;
    }
    
    .section-title {
        text-align: center;
        text-style: bold italic;
        color: $secondary;
        width: 100%;
        margin: 1 0;
    }
    """

    def compose(self) -> ComposeResult:
        """Create the layout using clean ``with`` syntax."""
        # ----- Using ``with`` syntax -----
        with Accordion("Accordion 1", id="histogram-accordion"):
            yield Static("Histogram", classes="section-title")

            with Vertical():
                # RadioGroup for Y‑Axis selection
                yield RadioGroup(
                    label="Y-Axis",
                    options=["Frequency", "Probabilistic"],
                    default="Probabilistic",
                    id="Y-Axis",
                )
                # DropBox for selecting which statistics to show
                yield DropBox(
                    label="Show",
                    options=["Mean", "Median", "Statistics", "Normal Distribution"],
                    selected=["Mean"],
                    id="show-dropdown",
                )
                # InputBox for bin size entry
                yield InputBox(
                    label="Bin size",
                    placeholder="type here...",
                    id="bin-size"
                )
                # RadioGroup for choosing the plot fallback backend
                yield RadioGroup(
                    label="Fallback",
                    options=["Sixel", "Plotext"],
                    default="Plotext",
                    id="_fallback",
                )


# ──────────────────────────────────────────────────────────────────────────────
# ENTRY POINT
# ──────────────────────────────────────────────────────────────────────────────


if __name__ == "__main__":
    # Create and run the application
    app = AccordionDemoApp()
    app.run()
