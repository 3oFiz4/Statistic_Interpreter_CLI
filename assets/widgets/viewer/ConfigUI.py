import json
import copy
import os
from pathlib import Path
from typing import Any, Optional

from textual import on, work
from textual.app import App, ComposeResult
from textual.screen import ModalScreen, Screen
from textual.widget import Widget
from textual.widgets import (
    Header,
    Footer,
    Static,
    Button,
    Checkbox,
    Input,
    Select,
    Label,
    Rule,
)
from textual.containers import (
    Container,
    Vertical,
    Horizontal,
    VerticalScroll,
    Center,
)
from textual.binding import Binding
from textual.css.query import NoMatches
from textual.reactive import reactive


# CSS
CONFIG_UI_CSS = """
/* ── ConfirmQuitModal ── */

ConfirmQuitModal {
    align: center middle;
    background: rgba(0, 0, 0, 0.85);
}

ConfirmQuitModal > #confirm-dialog {
    width: 50;
    height: 11;
    border: solid $primary;
    background: black;
    padding: 1 2;
}

ConfirmQuitModal #confirm-title {
    text-align: center;
    color: $primary;
    text-style: bold;
    width: 100%;
    margin-bottom: 1;
}

ConfirmQuitModal #confirm-message {
    text-align: center;
    color: white;
    width: 100%;
    margin-bottom: 1;
}

ConfirmQuitModal #confirm-buttons {
    align: center middle;
    height: 3;
    width: 100%;
}

ConfirmQuitModal .confirm-btn {
    margin: 0 1;
    min-width: 12;
    background: black;
    color: white;
    border: solid white;
}

ConfirmQuitModal .confirm-btn:hover {
    background: $primary;
    color: white;
}

ConfirmQuitModal .confirm-btn:focus {
    background: $primary;
    color: white;
    border: solid $primary;
}

/* ── ConfigUI main screen ── */
ConfigUI {
    align: center middle;
    background: rgba(0, 0, 0, 0.50);
}

ConfigUI > #config-outer {
    width: 80%;
    height: 80%;
    background: black;
    border: solid $primary;
    layers: default overlay;  /* ← ADD THIS */
}

ConfigUI > #config-outer {
    width: 80%;
    height: 80%;
    background: black;
    border: solid $primary;
}

ConfigUI #config-header-bar {
    dock: top;
    height: 3;
    background: black;
    border-bottom: solid $primary;
}

ConfigUI #config-title {
    text-align: center;
    color: $primary;
    text-style: bold;
    width: 100%;
}

ConfigUI #config-footer-bar {
    dock: bottom;
    height: 3;
    background: black;
    border-top: solid $primary;
    padding: 0 2;
}

ConfigUI #config-footer-text {
    color: white;
    text-align: center;
    width: 100%;
    padding: 1 0;
}

ConfigUI #config-scroll {
    background: black;
    margin: 0;
    padding: 1 2;
    height: 1fr;  
}

/* ── Section headers ── */
ConfigUI .section-header {
    color: $primary;
    text-style: bold;
    text-align: center;
    width: 100%;
    margin: 1 0 0 0;
    padding: 0;
}

ConfigUI .section-rule {
    color: $primary;
    margin: 0 0 0 0;
}

/* ── Field rows ── */
ConfigUI .field-row {
    height: auto;
    margin: 0 0;
    padding: 0 0;
    align: left middle;
    width: 100%;
    max-height: 5;
}

ConfigUI .field-label {
    color: white;
    width: 30;
    width: auto;       
    max-width: 30;     
    min-width: 12;     
    text-align: right;
}

ConfigUI .field-control {
    min-width: 15;
    width: 1fr;
    margin: 0 0;
}

/* ── Checkbox styling ── */
ConfigUI Checkbox {
    background: black;
    color: white;
    border: none;
    padding: 0 1;
    height: 1;
}

ConfigUI Checkbox:focus {
    background: black;
    color: $primary;
}

ConfigUI Checkbox > .toggle--button {
    color: white;
    background: black;
}

ConfigUI Checkbox.-on > .toggle--button {
    color: $primary;
}

/* ── Input styling ── */
ConfigUI Input {
    background: black;
    color: white;
    border: solid white;
    height: 3;
    margin: 0;
    padding: 0 1;
}

ConfigUI Input:focus {
    border: solid $primary;
    color: white;
}

/* ── Select styling ── */
ConfigUI Select {
    background: black;
    color: white;
    height: 3;
    margin: 0;
}

ConfigUI Select:focus {
    border: solid $primary;
}

ConfigUI Select > SelectCurrent {
    background: black;
    color: white;
    border: solid white;
}

ConfigUI Select:focus > SelectCurrent {
    border: solid $primary;
}

ConfigUI SelectOverlay {
    background: black;
    color: white;
    border: solid $primary;
}

ConfigUI SelectOverlay:focus > .option-list--option-highlighted {
    background: $primary;
    color: white;
}

/* ── Indented containers for nested sections ── */
ConfigUI .section-container {
    margin: 0 0 0 2;
    padding: 0;
    width: 100%;
}

/* ── Status bar ── */
ConfigUI #status-bar {
    dock: bottom;
    height: 1;
    background: black;
    color: $primary;
    text-align: center;
    width: 100%;
}

ConfigUI Footer {
    background: black;
    color: white;
}

ConfigUI Footer > .footer--key {
    background: $primary;
    color: white;
}
"""


class ConfigField:
    """Single parsed config. field"""

    BOOL = "bool"
    INPUT = "input"
    LIST = "list"
    HEADER = "header"

    def __init__(
        self,
        field_type: str,
        key: str,
        display_name: str,
        value: Any = None,
        default: Any = None,
        options: list = None,
        children: list = None,
        depth: int = 0,
    ):
        self.field_type = field_type
        self.key = key
        self.display_name = display_name
        self.value = value
        self.default = default
        self.options = options or []
        self.children = children or []
        self.depth = depth


def parse_config_json(data: dict, depth: int = 0) -> list[ConfigField]:
    """
    Parse JSON into a list of ConfigField objects.

    RULES!:
        - Key starting with '#' => HEADER, value must be dict, parsed recursively.
        - Key ending with ':input' => INPUT text field.
        - Key ending with ':list' => SELECT/OptionList with 'default' and 'list'.
        - Boolean value => CHECKBOX.
        - may add more...
    """
    fields = []

    for raw_key, raw_value in data.items():
        # ── Header ──
        if raw_key.startswith("#"):
            display_name = raw_key[1:].strip()  # it always on "#thisIsAKey"
            children = []
            if isinstance(raw_value, dict):
                children = parse_config_json(raw_value, depth=depth + 1)
            field = ConfigField(
                field_type=ConfigField.HEADER,
                key=raw_key,
                display_name=display_name,
                children=[],  # a header cannot have sub-header btw. ill make this a feature in the future
                depth=depth,
            )
            fields.append(field)

            # parse inner dict at SAME depth, append directly
            if isinstance(raw_value, dict):
                inner_fields = parse_config_json(raw_value, depth=depth)
                fields.extend(inner_fields)

        elif raw_key.endswith(":input"):
            display_name = raw_key.replace(
                ":input", ""
            ).strip()  # goes like this "visiblity:input"
            field = ConfigField(
                field_type=ConfigField.INPUT,
                key=raw_key,
                display_name=display_name,
                value=str(raw_value) if raw_value is not None else "",
                depth=depth,
            )
            fields.append(field)

        elif raw_key.endswith(":list"):
            display_name = raw_key.replace(":list", "").strip()
            default_val = ""
            option_list = []
            if isinstance(raw_value, dict):
                default_val = raw_value.get("default", "")
                option_list = raw_value.get("list", [])
            field = ConfigField(
                field_type=ConfigField.LIST,
                key=raw_key,
                display_name=display_name,
                value=default_val,
                default=default_val,
                options=option_list,
                depth=depth,
            )
            fields.append(field)

        elif isinstance(raw_value, bool):
            display_name = raw_key.strip()
            field = ConfigField(
                field_type=ConfigField.BOOL,
                key=raw_key,
                display_name=display_name,
                value=raw_value,
                depth=depth,
            )
            fields.append(field)

        # Fallback: treat as input.. Incase...
        else:
            display_name = raw_key.strip()
            field = ConfigField(
                field_type=ConfigField.INPUT,
                key=raw_key,
                display_name=display_name,
                value=str(raw_value) if raw_value is not None else "",
                depth=depth,
            )
            fields.append(field)

    return fields


def fields_to_json(fields: list[ConfigField]) -> dict:
    """Convert the ConfigField field objects back into JSON-serializable dict."""
    result = {}
    for field in fields:
        if field.field_type == ConfigField.HEADER:
            result[field.key] = fields_to_json(field.children)
        elif field.field_type == ConfigField.BOOL:
            result[field.key] = field.value
        elif field.field_type == ConfigField.INPUT:
            result[field.key] = field.value
        elif field.field_type == ConfigField.LIST:
            result[field.key] = {
                "default": field.value,
                "list": field.options,
            }
    return result


# Confirm Quit Modal
class ConfirmQuitOverlay(Widget):
    DEFAULT_CSS = """
    ConfirmQuitOverlay {
        dock: bottom;
        layer: overlay;
        width: 100%;
        height: 100%;
        align: center middle;
        background: rgba(0, 0, 0, 0.85);
    }

    ConfirmQuitOverlay #confirm-dialog {
        width: 50;
        height: 11;
        border: solid #ff0000;
        background: black;
        padding: 1 2;
    }

    ConfirmQuitOverlay #confirm-title {
        text-align: center;
        color: #ff0000;
        text-style: bold;
        width: 100%;
        margin-bottom: 1;
    }

    ConfirmQuitOverlay #confirm-message {
        text-align: center;
        color: white;
        width: 100%;
        margin-bottom: 1;
    }

    ConfirmQuitOverlay #confirm-buttons {
        align: center middle;
        height: 3;
        width: 100%;
    }

    ConfirmQuitOverlay .confirm-btn {
        margin: 0 1;
        min-width: 12;
        background: black;
        color: white;
        border: solid white;
    }

    ConfirmQuitOverlay .confirm-btn:hover {
        background: #ff0000;
        color: white;
    }

    ConfirmQuitOverlay .confirm-btn:focus {
        background: #ff0000;
        color: white;
        border: solid #ff0000;
    }
    """

    def compose(self) -> ComposeResult:
        with Container(id="confirm-dialog"):
            yield Static("⚠  Quit Config", id="confirm-title")
            yield Static("Are you sure? (Y / N)", id="confirm-message")
            with Horizontal(id="confirm-buttons"):
                yield Button("Yes (Y)", id="btn-yes", classes="confirm-btn")
                yield Button("No  (N)", id="btn-no", classes="confirm-btn")

    @on(Button.Pressed, "#btn-yes")
    def on_yes(self) -> None:
        config_ui = self.ancestors[-2]  # or use self.screen
        self.remove()
        self.screen.dismiss(False)

    @on(Button.Pressed, "#btn-no")
    def on_no(self) -> None:
        self.remove()


# ConfigUI Screen
class ConfigUI(ModalScreen[bool]):
    """
    Opens on top of any existing screen at 80%×80% with 50% transparency
    on the background. Parses a JSON file and renders controls.

    Keybindings:
        w  – Save and reload the app.
        q  – Quit (with confirmation).
        U  – Reset to default.json.
        u  – Undo last change.
        - may add more...
    """

    CSS = CONFIG_UI_CSS

    BINDINGS = [
        Binding("w", "save_config", "Save & Reload", show=True, priority=True),
        Binding("q", "quit_config", "Quit", show=True, priority=True),
        Binding(
            "Q", "quit_config_instant", "Quit instantly", show=True, priority=False
        ),
        Binding(
            "U",
            "reset_default",
            "Reset Default",
            show=True,
            key_display="shift+u",
            priority=True,
        ),
        Binding("u", "undo", "Undo", show=True, priority=True),
    ]

    def __init__(
        self,
        file_path: str,
        default_path: str | None = None,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        super().__init__(name=name, id=id, classes=classes)
        self.file_path = Path(file_path)
        if default_path is not None:
            self.default_path = Path(default_path)
        else:
            # Let's just say that the default.json might sits beside the config file
            self.default_path = self.file_path.parent / "default.json"
        self.config_data: dict = {}
        self.fields: list[ConfigField] = []
        self.undo_stack: list[dict] = []
        self._widget_map: dict[str, Widget] = {}  # widget_id -> field_key mapping
        self._field_index: dict[str, ConfigField] = {}  # flat index by unique id
        self._load_file()  # ← Load HERE, before compose()

    # LIFECYCLE
    def on_mount(self) -> None:
        pass

    def _load_file(self) -> None:
        """Load then parse the JSON config file."""
        if not self.file_path.exists():
            self.notify(
                f"File not found: {self.file_path}", severity="error", timeout=4
            )
            return
        if self.file_path.suffix.lower() != ".json":
            self.notify("File must be .json format", severity="error", timeout=4)
            return
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                self.config_data = json.load(f)
        except json.JSONDecodeError as e:
            self.notify(f"JSON parse error: {e}", severity="error", timeout=4)
            return

        self.fields = parse_config_json(self.config_data)
        self._push_undo()

    # COMPOSE
    def compose(self) -> ComposeResult:
        with Container(id="config-outer"):
            # Title bar
            with Container(id="config-header-bar"):
                yield Static(
                    f"Config ─ {self.file_path.name}",
                    id="config-title",
                )
            # Scrollable body
            with VerticalScroll(id="config-scroll"):
                yield from self._build_fields(self.fields)
            # Status / footer
            yield Footer()

    # WIDGET BUILDERS
    def _build_fields(
        self, fields: list[ConfigField], prefix: str = ""
    ) -> list[Widget]:
        """Recursively build widgets for a list of ConfigField objects."""
        widgets: list[Widget] = []

        for idx, field in enumerate(fields):
            uid = f"{prefix}{idx}_{field.key}"
            safe_id = self._safe_id(uid)
            self._field_index[safe_id] = field

            if field.field_type == ConfigField.HEADER:
                widgets.append(Rule(line_style="heavy", classes="section-rule"))
                widgets.append(
                    Static(
                        f"── {field.display_name} ──",
                        classes="section-header",
                    )
                )
                widgets.append(Rule(line_style="heavy", classes="section-rule"))
                child_container = Vertical(
                    *self._build_fields(field.children, prefix=f"{safe_id}_"),
                    classes="section-container",
                )
                widgets.append(child_container)

            elif field.field_type == ConfigField.BOOL:
                checkbox = Checkbox(
                    field.display_name,
                    value=bool(field.value),
                    id=f"chk_{safe_id}",
                    classes="field-control",
                )
                self._widget_map[f"chk_{safe_id}"] = field
                row = Horizontal(
                    Label(field.display_name, classes="field-label"),
                    checkbox,
                    classes="field-row",
                )
                widgets.append(row)

            elif field.field_type == ConfigField.INPUT:
                inp = Input(
                    value=str(field.value),
                    placeholder=field.display_name,
                    id=f"inp_{safe_id}",
                    classes="field-control",
                )
                self._widget_map[f"inp_{safe_id}"] = field
                row = Horizontal(
                    Label(field.display_name, classes="field-label"),
                    inp,
                    classes="field-row",
                )
                widgets.append(row)

            elif field.field_type == ConfigField.LIST:
                # Build options: include default + list items (deduplicated, ordered)
                all_options = []
                if field.value and field.value not in field.options:
                    all_options.append(field.value)
                all_options.extend(field.options)
                # Remove duplicates while preserving order
                seen = set()
                unique_options = []
                for opt in all_options:
                    if opt not in seen:
                        seen.add(opt)
                        unique_options.append(opt)

                select = Select(
                    options=[(o, o) for o in unique_options],
                    value=field.value if field.value else Select.BLANK,
                    id=f"sel_{safe_id}",
                    classes="field-control",
                    allow_blank=False,
                )
                self._widget_map[f"sel_{safe_id}"] = field
                row = Horizontal(
                    Label(field.display_name, classes="field-label"),
                    select,
                    classes="field-row",
                )
                widgets.append(row)

        return widgets

    @staticmethod
    def _safe_id(raw: str) -> str:
        """Convert a raw string into a valid Textual widget ID."""
        safe = ""
        for ch in raw:
            if ch.isalnum() or ch == "_" or ch == "-":
                safe += ch
            else:
                safe += "_"
        # Ensure it starts with a letter or underscore
        if safe and not (safe[0].isalpha() or safe[0] == "_"):
            safe = "f_" + safe
        if not safe:
            safe = "f_unknown"
        return safe

    # UNDO MANAGEMENT
    def _push_undo(self) -> None:
        """Snapshot current fields to undo stack."""
        snapshot = fields_to_json(self.fields)
        self.undo_stack.append(copy.deepcopy(snapshot))

    def _collect_current_values(self) -> None:
        """Read all widget values back into the field objects."""
        self._collect_from_fields(self.fields)

    def _collect_from_fields(self, fields: list[ConfigField], prefix: str = "") -> None:
        for idx, field in enumerate(fields):
            uid = f"{prefix}{idx}_{field.key}"
            safe_id = self._safe_id(uid)

            if field.field_type == ConfigField.HEADER:
                self._collect_from_fields(field.children, prefix=f"{safe_id}_")

            elif field.field_type == ConfigField.BOOL:
                try:
                    chk = self.query_one(f"#chk_{safe_id}", Checkbox)
                    field.value = chk.value
                except NoMatches:
                    pass

            elif field.field_type == ConfigField.INPUT:
                try:
                    inp = self.query_one(f"#inp_{safe_id}", Input)
                    field.value = inp.value
                except NoMatches:
                    pass

            elif field.field_type == ConfigField.LIST:
                try:
                    sel = self.query_one(f"#sel_{safe_id}", Select)
                    if sel.value is not Select.BLANK:
                        field.value = sel.value
                except NoMatches:
                    pass

    # EVENT HANDLERS
    @on(Checkbox.Changed)
    def on_checkbox_changed(self, event: Checkbox.Changed) -> None:
        """Track changes for undo."""
        self._collect_current_values()
        self._push_undo()

    @on(Input.Changed)
    def on_input_changed(self, event: Input.Changed) -> None:
        """Track changes for undo."""
        self._collect_current_values()
        self._push_undo()

    @on(Select.Changed)
    def on_select_changed(self, event: Select.Changed) -> None:
        """Track changes for undo."""
        self._collect_current_values()
        self._push_undo()

    # ACTIONS
    def action_save_config(self) -> None:
        """Save (w): Write current values to JSON and reload the app."""
        self._collect_current_values()
        output = fields_to_json(self.fields)
        try:
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump(output, f, indent=4, ensure_ascii=False)
            self.notify("Config saved ✓", severity="information", timeout=2)
        except OSError as e:
            self.notify(f"Save failed: {e}", severity="error", timeout=4)
            return

        # Dismiss and signal the app to reload
        self.dismiss(True)

    def action_quit_config(self) -> None:
        """Quit (q): Prompt for confirmation before closing."""
        existing = self.query("ConfirmQuitOverlay")
        if existing:
            return
        outer = self.query_one("#config-outer", Container)
        outer.mount(ConfirmQuitOverlay())

    def action_quit_config_instant(self) -> None:
        """Quit Hard (q!): No confirmation"""
        self.remove()
        self.screen.dismiss(False)

    def action_reset_default(self) -> None:
        """Reset to default (U): Load default.json and repopulate."""
        if not self.default_path.exists():
            self.notify(
                f"Default file not found: {self.default_path}",
                severity="error",
                timeout=4,
            )
            return
        try:
            with open(self.default_path, "r", encoding="utf-8") as f:
                default_data = json.load(f)
        except json.JSONDecodeError as e:
            self.notify(f"Default JSON error: {e}", severity="error", timeout=4)
            return

        self._collect_current_values()
        self._push_undo()

        self.config_data = default_data
        self.fields = parse_config_json(self.config_data)
        self._rebuild_ui()
        self.notify("Reset to defaults ✓", severity="warning", timeout=2)

    def action_undo(self) -> None:
        """Undo (u): Revert to the previous state."""
        if len(self.undo_stack) <= 1:
            self.notify("Nothing to undo", severity="warning", timeout=2)
            return
        # Pop current state
        self.undo_stack.pop()
        # Restore previous
        previous = copy.deepcopy(self.undo_stack[-1])
        self.config_data = previous
        self.fields = parse_config_json(self.config_data)
        self._rebuild_ui()
        self.notify("Undo ✓", severity="information", timeout=2)

    def _rebuild_ui(self) -> None:
        """Clear and rebuild the scrollable content area."""
        self._widget_map.clear()
        self._field_index.clear()

        try:
            scroll = self.query_one("#config-scroll", VerticalScroll)
        except NoMatches:
            return

        scroll.remove_children()
        new_widgets = self._build_fields(self.fields)
        for w in new_widgets:
            scroll.mount(w)


# Standalone testing
class DemoApp(App):
    CSS = """
    Screen {
        background: #1a1a1a;
    }

    #demo-label {
        width: 100%;
        height: 100%;
        content-align: center middle;
        text-align: center;
        color: white;
    }
    """

    BINDINGS = [
        Binding("c", "open_config", "Open Config"),
    ]

    def compose(self) -> ComposeResult:
        yield Static(
            "Demo App — Press [bold red]C[/bold red] to open Config UI",
            id="demo-label",
        )

    def action_open_config(self) -> None:
        def on_config_dismiss(should_reload: bool) -> None:
            if should_reload:
                self.notify("App reloading with new config...", timeout=3)
                # In a real app you'd reload state here

        self.push_screen(
            ConfigUI("config.json", default_path="default.json"),
            callback=on_config_dismiss,
        )


def _create_sample_files() -> None:
    """Create sample config.json and default.json for testing."""
    sample_config = {
        "#General": {
            "username:input": "user",
            "darkMode": False,
            "language:list": {
                "default": "English",
                "list": ["English", "Spanish", "French", "German", "Japanese"],
            },
            "autoSave": True,
        },
        "#Display": {
            "fullscreen": False,
            "resolution:list": {
                "default": "1920x1080",
                "list": ["1280x720", "1920x1080", "2560x1440", "3840x2160"],
            },
            "fontSize:input": "12",
        },
        "#Advanced": {
            "vsync": True,
            "antiAliasing:list": {
                "default": "FXAA",
                "list": ["None", "FXAA", "MSAA", "TAA"],
            },
            "renderScale:input": "1.0",
        },
        "#Network": {
            "proxyEnabled": False,
            "proxyAddress:input": "",
            "proxyPort:input": "8080",
            "timeout:list": {
                "default": "30s",
                "list": ["10s", "30s", "60s", "120s"],
            },
        },
        "notifications": True,
        "logLevel:list": {
            "default": "INFO",
            "list": ["DEBUG", "INFO", "WARNING", "ERROR"],
        },
    }

    sample_default = {
        "#General": {
            "username:input": "user",
            "darkMode": False,
            "language:list": {
                "default": "English",
                "list": ["English", "Spanish", "French", "German", "Japanese"],
            },
            "autoSave": True,
        },
        "#Display": {
            "fullscreen": False,
            "resolution:list": {
                "default": "1920x1080",
                "list": ["1280x720", "1920x1080", "2560x1440", "3840x2160"],
            },
            "fontSize:input": "12",
        },
        "#Advanced": {
            "vsync": True,
            "antiAliasing:list": {
                "default": "FXAA",
                "list": ["None", "FXAA", "MSAA", "TAA"],
            },
            "renderScale:input": "1.0",
        },
        "#Network": {
            "proxyEnabled": False,
            "proxyAddress:input": "",
            "proxyPort:input": "8080",
            "timeout:list": {
                "default": "30s",
                "list": ["10s", "30s", "60s", "120s"],
            },
        },
        "notifications": True,
        "logLevel:list": {
            "default": "INFO",
            "list": ["DEBUG", "INFO", "WARNING", "ERROR"],
        },
    }

    if not Path("config.json").exists():
        with open("config.json", "w", encoding="utf-8") as f:
            json.dump(sample_config, f, indent=4)
        print("Created sample config.json")

    if not Path("default.json").exists():
        with open("default.json", "w", encoding="utf-8") as f:
            json.dump(sample_default, f, indent=4)
        print("Created sample default.json")


if __name__ == "__main__":
    _create_sample_files()
    app = DemoApp()
    app.run()
