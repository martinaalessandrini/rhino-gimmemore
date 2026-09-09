"""Entry point for Rhino Library Plugin.

Usage in Rhino 8 Python:
    import sys
    sys.path.append(r"C:\\path\\to\\RhinoLibraryPlugin")
    from plugin import OnLoadPlugIn, RunCommand
    OnLoadPlugIn()
    # or RunCommand(True)
"""

import clr
clr.AddReference("Eto")
clr.AddReference("RhinoCommon")
clr.AddReference("RhinoUI")

import Rhino
import Rhino.UI
from ui.library_panel import LibraryPanel


# Global panel instance reference
_library_panel = None


def RunCommand(is_interactive):
    """Rhino command to show the Library Panel."""
    global _library_panel
    if _library_panel is None:
        _library_panel = LibraryPanel()
        Rhino.UI.Panels.RegisterPanel(
            None,
            _library_panel,
            "Libreria Interni",
            None
        )
    Rhino.UI.Panels.OpenPanel(_library_panel.Id)
    return Rhino.Commands.Result.Success


def OnLoadPlugIn():
    """Called when plugin loads. Registers the dockable panel."""
    global _library_panel
    _library_panel = LibraryPanel()
    Rhino.UI.Panels.RegisterPanel(None, _library_panel, "Libreria Interni", None)
    return True


# Auto-load if running as script
if __name__ == "__main__":
    OnLoadPlugIn()
