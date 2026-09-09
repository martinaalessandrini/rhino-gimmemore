import os

from core.model_entry import ModelEntry
from settings.plugin_settings import PluginSettings


class ThumbnailManager(object):
    """Manages thumbnail discovery and generation via Rhino APIs."""

    def __init__(self, settings):
        self.settings = settings

    def get_thumbnail_path(self, entry):
        if entry.thumbnail_path and os.path.exists(entry.thumbnail_path):
            return entry.thumbnail_path
        default_thumb = os.path.join(os.path.dirname(entry.file_path), entry.model_name + ".thumb.png")
        if os.path.exists(default_thumb):
            return default_thumb
        return None

    def generate_thumbnail(self, entry):
        if not self.settings.auto_generate_thumbnails:
            return None
        thumb_path = os.path.join(os.path.dirname(entry.file_path), entry.model_name + ".thumb.png")
        if os.path.exists(thumb_path):
            return thumb_path
        try:
            import clr
            clr.AddReference("RhinoCommon")
            import Rhino
            import System
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

            if doc.Views.Count > 0:
                view = doc.Views[0]
            else:
                view = doc.Views.Add("Thumbnail", Rhino.Display.DefinedViewProjection.Perspective)
            if view is None:
                doc.Dispose()
                return None

            size = self.settings.thumbnail_size
            bitmap = view.CaptureToBitmap(System.Drawing.Size(size, size))
            if bitmap is None:
                doc.Dispose()
                return None

            bitmap.Save(thumb_path)
            bitmap.Dispose()
            doc.Dispose()
            return thumb_path
        except Exception:
            return None
