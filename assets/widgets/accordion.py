"""
Features:
- Centered title with '|' character background fill
- Automatic width with height of 1 for the header
- Content persists in DOM when hidden (just visually hidden)
- Custom RadioGroup, DropBox, and InputBox widgets
"""

from textual.app import App, ComposeResult
from textual.widgets import Static, Input, Checkbox, RadioButton, RadioSet, Label
from textual.containers import Vertical, Container
from textual.widget import Widget
from textual.events import Click
from textual.reactive import reactive


# ═══════════════════════════════════════════════════════════════════════════════
# CUSTOM INPUT WIDGETS
# ═══════════════════════════════════════════════════════════════════════════════


class RadioGroup(Container):
    """
    A labeled group of radio buttons where only one option can be selected.
    
    Args:
        label: Display label for the group
        options: List of option strings
        default: The default selected option
        id: Widget identifier
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
        self._label = label          # Store the label text
        self._options = options      # Store available options
        self._default = default      # Store the default selection
    
    def compose(self) -> ComposeResult:
        """Build the radio group structure."""
        # Label above the radio buttons
        yield Label(self._label)
        
        # RadioSet containing all radio buttons
        with RadioSet():
            for option in self._options:
                # Set value=True for the default option
                is_default = (option == self._default)
                yield RadioButton(option, value=is_default)


class DropBox(Container):
    """
    A multi-select dropdown implemented with checkboxes.
    Multiple options can be selected simultaneously.
    
    Args:
        label: Display label for the dropdown
        options: List of option strings
        selected: List of pre-selected options
        id: Widget identifier
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
        self._selected = selected or []  # Default to empty list if None
    
    def compose(self) -> ComposeResult:
        """Build the checkbox dropdown structure."""
        yield Label(self._label)
        
        # Vertical container for checkboxes
        with Vertical():
            for option in self._options:
                # Check if this option should be pre-selected
                is_selected = option in self._selected
                yield Checkbox(option, value=is_selected)


class InputBox(Container):
    """
    A labeled text input field.
    
    Args:
        label: Display label for the input
        placeholder: Placeholder text shown when input is empty
        id: Widget identifier
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


# ═══════════════════════════════════════════════════════════════════════════════
# ACCORDION WIDGET COMPONENTS
# ═══════════════════════════════════════════════════════════════════════════════


class AccordionHeader(Static, can_focus=True):
    """
    The clickable header bar of the Accordion.
    
    Displays the title centered with '|' characters filling the background.
    Height is fixed at 1 row, width adjusts automatically.
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
        self._title = title
    
    def on_mount(self) -> None:
        """Initialize the display when widget is mounted."""
        self._render_title()
    
    def on_resize(self) -> None:
        """Re-render title when widget size changes."""
        self._render_title()
    
    def _render_title(self) -> None:
        """
        Render the accordion title with '|' background pattern.
        
        The title is centered within the available width, with '|'
        characters filling the remaining space on both sides.
        
        Example output: "||||||||| Accordion 1 |||||||||"
        """
        width = self.size.width
        
        # Guard against zero or negative width
        if width <= 0:
            return
        
        # Add spaces around the title for visual separation
        title_with_padding = f" {self._title} "
        title_length = len(title_with_padding)
        
        # Calculate fill characters needed on each side
        remaining_space = max(0, width - title_length)
        left_fill = remaining_space // 2      # Left side fill count
        right_fill = remaining_space - left_fill  # Right side (handles odd widths)
        
        # Construct the final display string
        # Format: ||||||| Title |||||||
        display_text = ("|" * left_fill) + title_with_padding + ("|" * right_fill)
        
        # Update the widget content
        self.update(display_text)


class AccordionBody(Container):
    """
    The content container of the Accordion.
    
    This container holds all the accordion's content and is hidden/shown
    based on the accordion's expanded state. Items remain in the DOM
    even when hidden.
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
    
    Supports two ways to add content:
    
    1. Using `with` syntax:
        with Accordion("Title"):
            yield Widget1()
            yield Widget2()
    
    2. Using constructor arguments:
        yield Accordion("Title", Widget1(), Widget2())
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
        # Store children passed via constructor OR collected via `with` syntax
        self._accordion_children: list[Widget] = list(children)
        # Reference to body container
        self._body: AccordionBody | None = None
    
    def compose(self) -> ComposeResult:
        """Compose the accordion structure."""
        yield AccordionHeader(self._title)
        self._body = AccordionBody()
        yield self._body
    
    def compose_add_child(self, widget: Widget) -> None:
        """
        Called when widgets are yielded inside `with Accordion():` block.
        Collects children to be mounted later.
        """
        self._accordion_children.append(widget)
    
    def on_mount(self) -> None:
        """Mount all collected children to the body after accordion is ready."""
        if self._body and self._accordion_children:
            for child in self._accordion_children:
                self._body.mount(child)
            self._accordion_children.clear()
    
    def watch_expanded(self, expanded: bool) -> None:
        """Toggle the '-expanded' CSS class."""
        self.set_class(expanded, "-expanded")
    
    def on_click(self, event: Click) -> None:
        """Toggle only when header is clicked."""
        if isinstance(event.control, AccordionHeader):
            self.expanded = not self.expanded


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN APPLICATION
# ═══════════════════════════════════════════════════════════════════════════════


class AccordionDemoApp(App):
    """Demo application with clean `with` syntax."""
    
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
        """Create the layout using clean `with` syntax."""
        
        # ----- Using `with` syntax -----
        with Accordion("Accordion 1", id="histogram-accordion"):
            yield Static("Histogram", classes="section-title")
            
            with Vertical():
                yield RadioGroup(
                    label="Y-Axis",
                    options=["Frequency", "Probabilistic"],
                    default="Probabilistic",
                    id="Y-Axis",
                )
                yield DropBox(
                    label="Show",
                    options=["Mean", "Median", "Statistics", "Normal Distribution"],
                    selected=["Mean"],
                    id="show-dropdown",
                )
                yield InputBox(
                    label="Bin size",
                    placeholder="type here...",
                    id="bin-size"
                )
                yield RadioGroup(
                    label="Fallback",
                    options=["Sixel", "Plotext"],
                    default="Plotext",
                    id="_fallback",
                )


# ═══════════════════════════════════════════════════════════════════════════════
# ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════════


if __name__ == "__main__":
    # Create and run the application
    app = AccordionDemoApp()
    app.run()
