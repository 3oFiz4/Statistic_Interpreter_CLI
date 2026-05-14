from textual.theme import Theme

CRIMSON_TERMINAL = Theme(
    name="crimson_terminal",

    primary="#ff0000",
    secondary="#111",
    accent="#f00",

    foreground="#ffffff",
    background="#000000",

    surface="#000",
    panel="#000",

    success="#00ff00",
    warning="#ffaa00",
    error="#ff0000",

    dark=True,
)

def LoadTheme(self) -> None:
    self.register_theme(CRIMSON_TERMINAL)
    self.theme = "crimson_terminal"
