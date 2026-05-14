from __future__ import annotations

import threading
from pathlib import Path
from typing import Callable

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileModifiedEvent


class FileObserver:
    """
    Event-driven file watcher using watchdog library.
    Calls a callback when the watched file is modified.
    
    Usage:
        def on_change():
            print("File changed!")
        
        watcher = WatchdogFileWatcher("data.json", on_change)
        watcher.start()
        # ... later ...
        watcher.stop()
    """

    def __init__(
        self,
        filepath: str,
        on_modified_callback: Callable[[], None],
    ) -> None:
        self._filepath = Path(filepath).resolve()
        self._callback = on_modified_callback
        self._observer: Observer | None = None
        self._handler = _FileChangeHandler(self._filepath, self._callback)

    def start(self) -> None:
        """Start watching the file's directory."""
        if self._observer is not None:
            return

        self._observer = Observer()
        # Watch the directory containing the file
        watch_dir = str(self._filepath.parent)
        self._observer.schedule(self._handler, watch_dir, recursive=False)
        self._observer.start()

    def stop(self) -> None:
        """Stop watching."""
        if self._observer:
            self._observer.stop()
            self._observer.join()
            self._observer = None

    def set_file(self, filepath: str) -> None:
        """Change the file being watched."""
        was_running = self._observer is not None
        if was_running:
            self.stop()

        self._filepath = Path(filepath).resolve()
        self._handler = _FileChangeHandler(self._filepath, self._callback)

        if was_running:
            self.start()


class _FileChangeHandler(FileSystemEventHandler):
    """Internal handler that filters events to our specific file."""

    def __init__(self, filepath: Path, callback: Callable[[], None]) -> None:
        super().__init__()
        self._filepath = filepath
        self._callback = callback

    def on_modified(self, event: FileModifiedEvent) -> None:
        if event.is_directory:
            return
        # Check if this is our file
        event_path = Path(event.src_path).resolve()
        if event_path == self._filepath:
            self._callback()
