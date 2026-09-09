import os


class ImportManager(object):
    """Handles importing 3D models into the current Rhino document."""

    SUPPORTED_FORMATS = set([".obj", ".3ds", ".3dm"])

    def can_import(self, file_path):
        if not file_path or not os.path.exists(file_path):
            return False
        return os.path.splitext(file_path)[1].lower() in self.SUPPORTED_FORMATS

    def import_model(self, file_path):
        if not self.can_import(file_path):
            return False
        try:
            import clr
            clr.AddReference("RhinoCommon")
            import Rhino

            doc = Rhino.RhinoDoc.ActiveDoc
            if doc is None:
                return False

            command = '_-Import "{0}" _Enter'.format(file_path)
            return Rhino.RhinoApp.RunScript(command, False)
        except Exception:
            return False
