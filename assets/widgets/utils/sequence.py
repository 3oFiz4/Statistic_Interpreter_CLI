from textual import events


class SequenceBinding:
    """
    Mixin that adds vim-like key sequence support to Textual apps.

    Usage:
        class MyApp(KeySequenceMixin, App):
            SEQUENCES = [
                ("gs", "git_status", "Git Status"),
                ("ga", "git_add", "Git Add"),
            ]

            def action_git_status(self):
                ...
    """

    # Define sequences like Textual's BINDINGS: (keys, action, description)
    SEQUENCES: list[tuple[str, str, str]] = []

    # Timeout before falling back to single-key bindings
    SEQUENCE_TIMEOUT: float = 0.5

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._key_buffer: str = ""
        self._sequence_timer = None
        self._sequence_map: dict[str, str] = {}
        self._sequence_starters: set[str] = set()
        self._build_sequence_map()

    def _build_sequence_map(self) -> None:
        """Build lookup structures from SEQUENCES."""
        for keys, action, *_ in self.SEQUENCES:
            self._sequence_map[keys] = action
            self._sequence_starters.add(keys[0])

    def _get_possible_sequences(self, prefix: str) -> list[str]:
        """Get all sequences starting with prefix."""
        return [k for k in self._sequence_map if k.startswith(prefix)]

    def on_key(self, event: events.Key) -> None:
        """Intercept keys for sequence handling."""
        key = event.key

        # Skip special keys
        if len(key) > 1 and key not in self._sequence_starters:
            return

        potential = self._key_buffer + key

        # Already buffering
        if self._key_buffer:
            event.prevent_default()
            self._stop_timer()

            if potential in self._sequence_map:
                # Complete match - execute sequence action
                action = self._sequence_map[potential]
                self._clear_buffer()
                self.run_action(action)

            elif self._get_possible_sequences(potential):
                # Partial match - continue buffering
                self._key_buffer = potential
                self._start_timer()

            else:
                # No match - execute buffered keys then current
                self._flush_buffer(key)

        # Potential sequence starter
        elif key in self._sequence_starters:
            event.prevent_default()
            self._key_buffer = key
            self._start_timer()

    def _start_timer(self) -> None:
        """Start sequence timeout timer."""
        self._sequence_timer = self.set_timer(self.SEQUENCE_TIMEOUT, self._on_timeout)

    def _stop_timer(self) -> None:
        """Stop sequence timeout timer."""
        if self._sequence_timer:
            self._sequence_timer.stop()
            self._sequence_timer = None

    def _clear_buffer(self) -> None:
        """Clear key buffer."""
        self._key_buffer = ""
        self._stop_timer()

    def _on_timeout(self) -> None:
        """Handle sequence timeout - run buffered keys as single actions."""
        self._sequence_timer = None
        if self._key_buffer:
            buffered = self._key_buffer
            self._clear_buffer()
            for k in buffered:
                self.run_action(f"key_{k}")

    def _flush_buffer(self, current_key: str) -> None:
        """Flush buffer as single keys, then handle current key."""
        buffered = self._key_buffer
        self._clear_buffer()
        for k in buffered:
            self.run_action(f"key_{k}")
        self.run_action(f"key_{current_key}")
