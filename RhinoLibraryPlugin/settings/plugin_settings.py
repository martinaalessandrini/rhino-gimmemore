"""Persist user preferences in a JSON file in %APPDATA%/RhinoLibraryPlugin."""
import json
import os
from pathlib import Path


class PluginSettings:
    """Manages plugin settings persistence."""

    SETTINGS_DIR = Path(os.environ.get("APPDATA", Path.home())) / "RhinoLibraryPlugin"
    SETTINGS_FILE = SETTINGS_DIR / "settings.json"

    def __init__(self):
        self.library_root_path: str = ""
        self.auto_generate_thumbnails: bool = True
        self.thumbnail_size: int = 128
        self.load()

    def load(self) -> None:
        """Loads settings from disk."""
        if not self.SETTINGS_FILE.exists():
            return
        try:
            with open(self.SETTINGS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.library_root_path = data.get("libraryRootPath", "")
            self.auto_generate_thumbnails = data.get("autoGenerateThumbnails", True)
            self.thumbnail_size = data.get("thumbnailSize", 128)
        except Exception:
            pass

    def save(self) -> None:
        """Saves settings to disk."""
        self.SETTINGS_DIR.mkdir(parents=True, exist_ok=True)
        data = {
            "libraryRootPath": self.library_root_path,
            "autoGenerateThumbnails": self.auto_generate_thumbnails,
            "thumbnailSize": self.thumbnail_size
        }
        with open(self.SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
