from assets.widgets.utils.config_manager import (
    Config,
    JsonConfigSource,
)

# ── Config sources ──────────────────────
# Earlier = lower priority, later = overrides

_sources = [
    JsonConfigSource("config.json", required=True),
]

config = Config(*_sources).load()

# code imported from 3oFiz4/Discord-Message-Summarizer
