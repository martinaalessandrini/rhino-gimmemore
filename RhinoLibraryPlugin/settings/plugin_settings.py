import json
import os

try:
    import codecs
except ImportError:
    codecs = None


class PluginSettings(object):
    """Manages plugin settings persistence."""

    SETTINGS_DIR = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), "RhinoLibraryPlugin")
    SETTINGS_FILE = os.path.join(SETTINGS_DIR, "settings.json")

    def __init__(self, settings_file=None, default_to_fixture=True):
        self.library_root_path = ""
        self.auto_generate_thumbnails = True
        self.thumbnail_size = 128
        self._settings_file = settings_file or self.SETTINGS_FILE
        self.load()
        if default_to_fixture and not self.library_root_path:
            here = os.path.dirname(os.path.abspath(__file__))
            plugin_root = os.path.dirname(here)
            default_library = os.path.join(plugin_root, "tests", "fixtures", "libreria")
            if os.path.isdir(default_library):
                self.library_root_path = default_library

    def load(self):
        if not os.path.exists(self._settings_file):
            return
        try:
            try:
                f = open(self._settings_file, "r", encoding="utf-8-sig")
            except TypeError:
                f = codecs.open(self._settings_file, "r", "utf-8-sig")
            try:
                data = json.load(f)
            finally:
                f.close()
            self.library_root_path = data.get("libraryRootPath", "")
            self.auto_generate_thumbnails = data.get("autoGenerateThumbnails", True)
            self.thumbnail_size = data.get("thumbnailSize", 128)
        except Exception:
            pass

    def save(self):
        if not os.path.isdir(self.SETTINGS_DIR):
            os.makedirs(self.SETTINGS_DIR)
        data = {
            "libraryRootPath": self.library_root_path,
            "autoGenerateThumbnails": self.auto_generate_thumbnails,
            "thumbnailSize": self.thumbnail_size
        }
        try:
            f = open(self._settings_file, "w", encoding="utf-8")
        except TypeError:
            f = codecs.open(self._settings_file, "w", "utf-8")
        try:
            json.dump(data, f, indent=2, ensure_ascii=False)
        finally:
            f.close()
