# widgets/plot_container.py

from __future__ import annotations

import uuid

from textual.widget import Widget
from textual.reactive import reactive
from textual.app import ComposeResult
from textual.containers import Container
from textual.message import Message

from ..plot_callback import PlotCallback, PlotFallback, PlotType, PlotData


class PlotContainer(Widget):
    """
    A higher-level container widget that wraps PlotCallback and provides
    reactive fallback switching.

    When `fallback_mode` changes, the inner widget is replaced automatically.
    """

    DEFAULT_CSS = """
    PlotContainer {
        width: 100%;
        height: 100%;
    }

    PlotContainer #plot-inner {
        width: 100%;
        height: 100%;
    }
    """

    fallback_mode: reactive[str] = reactive("plotwidget", layout=True, init=False)

    class FallbackChanged(Message):
        def __init__(self, new_fallback: str) -> None:
            super().__init__()
            self.new_fallback = new_fallback

    def __init__(
        self,
        plot_callback: PlotCallback,
        *,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        super().__init__(id=id, classes=classes)
        self._plot_callback = plot_callback
        self._is_mounted = False
        # Set the reactive's default without triggering the watcher
        # by writing to the underlying storage directly
        self.set_reactive(PlotContainer.fallback_mode, plot_callback.fallback.value)

    def compose(self) -> ComposeResult:
        with Container(id="plot-inner"):
            yield self._create_widget()

    def on_mount(self) -> None:
        """Called after compose — DOM is now available."""
        self._is_mounted = True

    def watch_fallback_mode(self, new_value: str) -> None:
        """When fallback_mode reactive changes, rebuild the inner widget."""
        if not self._is_mounted:
            return

        self._plot_callback.set_fallback(new_value)
        self.post_message(self.FallbackChanged(new_value))
        self._rebuild()

    def _create_widget(self) -> Widget:
        """
        Create a new plot widget, ensuring a unique ID each time
        to avoid DuplicateIds errors on rebuild.
        """
        # Temporarily override the widget_id to a unique one
        original_id = self._plot_callback._widget_id
        unique_suffix = uuid.uuid4().hex[:8]

        if original_id:
            self._plot_callback._widget_id = f"{original_id}-{unique_suffix}"
        else:
            self._plot_callback._widget_id = f"plot-{unique_suffix}"

        widget = self._plot_callback.widget()

        # Restore the original so the user's config isn't permanently changed
        self._plot_callback._widget_id = original_id

        return widget

    def _rebuild(self) -> None:
        """Remove the old widget and mount the new one."""
        try:
            inner = self.query_one("#plot-inner", Container)
        except Exception:
            return
        inner.remove_children()
        inner.mount(self._create_widget())

    def update_data(
        self,
        x: list[float] | None = None,
        y: list[float] | None = None,
    ) -> None:
        """Update the underlying data and re-render."""
        if x is not None:
            self._plot_callback.x(x)
        if y is not None:
            self._plot_callback.y(y)
        self._rebuild()
