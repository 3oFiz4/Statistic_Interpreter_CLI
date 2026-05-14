"""
Live Tabs Component for Textual
Reusable, responsive tabs that fit within a terminal.
"""

from textual.app import App, ComposeResult
from textual.containers import Container
from textual.widgets import Static, TabbedContent, TabPane
from textual import on

# Assuming DropdownCheckboxButton exists in your project
from widget_dropdown_button import DropdownCheckboxButton

# ─────────────────────────────────────────────────────────────────────────────
# REUSABLE COMPONENTS
# ─────────────────────────────────────────────────────────────────────────────


class TabContent(Container):
    """
    Content component for individual tabs.
    Contains a DropdownCheckboxButton and output display.
    """

    DEFAULT_CSS = """
    TabContent {
        height: auto;
        width: 100%;
        padding: 1;
    }
    
    TabContent .output {
        height: 1;
        margin-top: 1;
        color: $text-muted;
    }
    """

    def __init__(
        self,
        label: str = "Fruits",
        options: list[str] | None = None,
        selected: list[str] | None = None,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self._label = label
        self._options = options or ["Apple", "Banana", "Cherry", "Date", "Fig", "Grape"]
        self._selected = selected or ["Apple"]

    def compose(self) -> ComposeResult:
        yield DropdownCheckboxButton(
            label=self._label,
            options=self._options,
            selected=self._selected,
        )
        yield Static("", classes="output")

    @on(DropdownCheckboxButton.Changed)
    def _on_changed(self, event: DropdownCheckboxButton.Changed) -> None:
        sel = ", ".join(event.selected) or "none"
        self.query_one(".output", Static).update(f"Selected: {sel}")


class LiveTabs(Container):
    """
    Reusable Live Tabs component.
    
    A responsive, terminal-sized tabs container that can be 
    embedded anywhere in your application.
    
    Usage:
        yield LiveTabs(
            tabs=[
                {"label": "Tab 1", "options": ["A", "B", "C"]},
                {"label": "Tab 2", "options": ["X", "Y", "Z"]},
            ]
        )
    """

    DEFAULT_CSS = """
    LiveTabs {
        height: auto;
        max-height: 100%;
        width: 100%;
    }
    
    LiveTabs TabbedContent {
        height: auto;
        max-height: 100%;
    }
    
    LiveTabs ContentSwitcher {
        height: auto;
    }
    
    LiveTabs TabPane {
        height: auto;
        padding: 0;
    }
    
    LiveTabs Tabs {
        width: 100%;
        dock: top;
    }
    
    LiveTabs Tab {
        padding: 0 2;
    }
    """

    def __init__(
        self,
        tabs: list[dict] | None = None,
        initial: str | None = None,
        **kwargs,
    ) -> None:
        """
        Initialize LiveTabs component.
        
        Args:
            tabs: List of tab configurations. Each dict can have:
                  - "label": Tab title (required)
                  - "dropdown_label": Label for dropdown (default: "Fruits")
                  - "options": List of dropdown options
                  - "selected": Initially selected options
            initial: ID of the initially active tab (e.g., "tab-0")
        """
        super().__init__(**kwargs)
        self._tabs = tabs or [
            {"label": "Tab 1"},
            {"label": "Tab 2"},
            {"label": "Tab 3"},
        ]
        self._initial = initial

    def compose(self) -> ComposeResult:
        initial = self._initial or "tab-0"
        
        with TabbedContent(initial=initial):
            for idx, tab_config in enumerate(self._tabs):
                tab_id = f"tab-{idx}"
                label = tab_config.get("label", f"Tab {idx + 1}")
                
                with TabPane(label, id=tab_id):
                    yield TabContent(
                        label=tab_config.get("dropdown_label", "Fruits"),
                        options=tab_config.get("options"),
                        selected=tab_config.get("selected"),
                        id=f"content-{tab_id}",
                    )


# ─────────────────────────────────────────────────────────────────────────────
# DEMO APPLICATION
# ─────────────────────────────────────────────────────────────────────────────


class LiveTabsDemo(App):
    """Demo application showcasing the LiveTabs component."""

    CSS = """
    Screen {
        padding: 1;
        align: center middle;
    }
    
    #main-tabs {
        border: round $primary;
        padding: 0;
    }
    """

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("1", "switch_tab('tab-0')", "Tab 1"),
        ("2", "switch_tab('tab-1')", "Tab 2"),
        ("3", "switch_tab('tab-2')", "Tab 3"),
    ]

    def compose(self) -> ComposeResult:
        yield LiveTabs(
            tabs=[
                {
                    "label": "Fruits",
                    "dropdown_label": "Fruits",
                    "options": ["Apple", "Banana", "Cherry", "Date", "Fig", "Grape"],
                    "selected": ["Apple"],
                },
                {
                    "label": "Vegetables",
                    "dropdown_label": "Vegetables",
                    "options": ["Carrot", "Broccoli", "Spinach", "Pepper", "Onion"],
                    "selected": ["Carrot", "Spinach"],
                },
                {
                    "label": "Beverages",
                    "dropdown_label": "Beverages",
                    "options": ["Coffee", "Tea", "Juice", "Water", "Soda"],
                    "selected": ["Coffee"],
                },
            ],
            id="main-tabs",
        )

    def action_switch_tab(self, tab_id: str) -> None:
        """Switch to a specific tab."""
        tabs = self.query_one(TabbedContent)
        tabs.active = tab_id


if __name__ == "__main__":
    app = LiveTabsDemo()
    app.run()
