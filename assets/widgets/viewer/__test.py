from ConfigUI import ConfigUI
from textual.app import App


class MyApp(App):
    def action_open_settings(self):
        def handle_result(saved: bool):
            if saved:
                self.reload_config()

        self.push_screen(
            ConfigUI("settings.json", default_path="defaults.json"),
            callback=handle_result,
        )
