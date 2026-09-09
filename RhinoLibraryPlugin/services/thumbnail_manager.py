from pathlib import Path
from typing import Optional

from core.model_entry import ModelEntry
from settings.plugin_settings import PluginSettings


class ThumbnailManager:
    """Manages thumbnail discovery and generation via Rhino APIs."""

    def __init__(self, settings: PluginSettings):
        self.settings = settings

    def get_thumbnail_path(self, entry: ModelEntry) -> Optional[str]:
        """Returns existing thumbnail path or None if not found."""
        if entry.thumbnail_path and Path(entry.thumbnail_path).exists():
            return entry.thumbnail_path

        default_thumb = Path(entry.file_path).parent / f"{entry.model_name}.thumb.png"
        return str(default_thumb) if default_thumb.exists() else None

    def generate_thumbnail(self, entry: ModelEntry) -> Optional[str]:
        """Generates thumbnail using Rhino APIs. Must be called within Rhino context."""
        if not self.settings.auto_generate_thumbnails:
            return None

        thumb_path = Path(entry.file_path).parent / f"{entry.model_name}.thumb.png"
        if thumb_path.exists():
            return str(thumb_path)

        try:
            import clr
            clr.AddReference("RhinoCommon")
            import Rhino
            from Rhino.FileIO import FileReadOptions

            doc = Rhino.RhinoDoc.CreateHeadless("temp")
            if doc is None:
                return None

            read_opts = FileReadOptions()
            read_opts.ImportMode = True
            success = doc.ReadFile(entry.file_path, read_opts)
            if not success:
                doc.Dispose()
                return None

            view = doc.Views[0] if doc.Views.Count > 0 else doc.Views.Add("Thumbnail", Rhino.Display.DefinedViewProjection.Perspective)
            if view is None:
                doc.Dispose()
                return None

            size = self.settings.thumbnail_size
            bitmap = view.CaptureToBitmap(
                System.Drawing.Size(size, size),
                Rhino.Display.CaptureMode.Opaque
            )
            if bitmap is None:
                doc.Dispose()
                return None

            bitmap.Save(str(thumb_path))
            bitmap.Dispose()
            doc.Dispose()
            return str(thumb_path)
        except Exception:
            return None
