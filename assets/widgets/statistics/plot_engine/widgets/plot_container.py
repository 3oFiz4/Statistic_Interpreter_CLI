# widgets/plot_container.py

"""
PlotContainer module.

Provides a high‑level Textual widget that wraps a PlotCallback instance.
It manages reactive fallback mode switching and ensures that the inner
plot widget is recreated with a unique identifier whenever the fallback
changes or the underlying data is updated.
"""

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
    A higher‑level container widget that wraps PlotCallback and provides
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

    # Reactive attribute that stores the current fallback mode.
    # `layout=True` ensures the layout is refreshed when it changes.
    # `init=False` prevents the default watcher from running on init.
    fallback_mode: reactive[str] = reactive("plotwidget", layout=True, init=False)

    class FallbackChanged(Message):
        """Message emitted when the fallback mode is changed."""
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
        """
        Initialise the PlotContainer.

        Parameters
        ----------
        plot_callback: PlotCallback
            The PlotCallback instance that knows how to build the actual plot widget.
        id, classes: optional Textual identifiers.
        """
        super().__init__(id=id, classes=classes)
        self._plot_callback = plot_callback
        self._is_mounted = False
        # Set the reactive's default without triggering the watcher
        # by writing directly to the underlying storage.
        self.set_reactive(PlotContainer.fallback_mode, plot_callback.fallback.value)

    def compose(self) -> ComposeResult:
        """
        Build the initial widget tree.

        Returns a Container with id "plot-inner" that will hold the inner plot widget.
        """
        with Container(id="plot-inner"):
            yield self._create_widget()

    def on_mount(self) -> None:
        """Called after compose — DOM is now available."""
        self._is_mounted = True

    def watch_fallback_mode(self, new_value: str) -> None:
        """
        Reactive watcher for `fallback_mode`.

        When the fallback mode changes:
        * Update the PlotCallback's fallback.
        * Emit a FallbackChanged message.
        * Rebuild the inner widget.
        """
        if not self._is_mounted:
            return

        self._plot_callback.set_fallback(new_value)
        self.post_message(self.FallbackChanged(new_value))
        self._rebuild()

    def _create_widget(self) -> Widget:
        """
        Create a new plot widget, ensuring a unique ID each time
        to avoid DuplicateIds errors on rebuild.

        The PlotCallback may store a widget_id; we temporarily replace it
        with a unique suffix, create the widget, then restore the original.
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
        """
        Remove the old widget from the inner container and mount a newly created one.
        """
        try:
            inner = self.query_one("#plot-inner", Container)
        except Exception:
            # If the container cannot be found, silently abort.
            return
        inner.remove_children()
        inner.mount(self._create_widget())

    def update_data(
        self,
        x: list[float] | None = None,
        y: list[float] | None = None,
    ) -> None:
        """
        Update the underlying data in the PlotCallback and re‑render.

        Parameters
        ----------
        x, y: optional new data series.
        """
        if x is not None:
            self._plot_callback.x(x)
        if y is not None:
            self._plot_callback.y(y)
        self._rebuild()
