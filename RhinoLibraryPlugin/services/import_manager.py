from pathlib import Path


class ImportManager:
    """Handles importing 3D models into the current Rhino document."""

    SUPPORTED_FORMATS = {".obj", ".3ds", ".3dm"}

    def can_import(self, file_path: str) -> bool:
        """Checks if the file format is supported and the file exists."""
        if not file_path or not Path(file_path).exists():
            return False
        return Path(file_path).suffix.lower() in self.SUPPORTED_FORMATS

    def import_model(self, file_path: str) -> bool:
        """Imports a model file into the active Rhino document. Must be called within Rhino context."""
        if not self.can_import(file_path):
            return False

        try:
            import clr
            clr.AddReference("RhinoCommon")
            import Rhino

            doc = Rhino.RhinoDoc.ActiveDoc
            if doc is None:
                return False

            command = f'_-Import "{file_path}" _Enter'
            return Rhino.RhinoApp.RunScript(command, False)
        except Exception:
            return False
