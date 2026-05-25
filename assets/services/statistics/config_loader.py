from pathlib import Path

def LoadConfig(self) -> None:
    """Load configuration from config.json."""
    config_path = Path("../../config.json")
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # Custom format for viewer
        if config.get("viewer_custom_formats", False):
            self.custom_formats = config.get("viewer_custom_formats_list", [])
            # Pre-compile regex patterns
            for fmt in self.custom_formats:
                fmt["_compiled"] = re.compile(fmt.get("regex", ""))
    except Exception as e:
        self.custom_formats = []
