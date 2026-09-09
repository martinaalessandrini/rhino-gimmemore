"""Entry point for Rhino Library Plugin (IronPython 2 / Rhino 8)."""
import clr

clr.AddReference("Eto")
clr.AddReference("RhinoCommon")

import Eto.Drawing as drawing
import Eto.Forms as forms
import Rhino.UI

from ui.library_panel import LibraryPanel

_library_form = None


class LibraryHostForm(forms.Form):
    def __init__(self):
        super(LibraryHostForm, self).__init__()
        self.Title = "Libreria Interni (cartella)"
        self.ClientSize = drawing.Size(460, 380)
        self.MinimumSize = drawing.Size(320, 260)
        self.Padding = drawing.Padding(6)
        self.Resizable = True
        self.Maximizable = True
        self.ShowInTaskbar = True
        self.Topmost = True
        self.Content = LibraryPanel()


def _reset_form(sender, e):
    global _library_form
    _library_form = None


def OnLoadPlugIn():
    global _library_form
    try:
        if _library_form is None:
            _library_form = LibraryHostForm()
            _library_form.Owner = Rhino.UI.RhinoEtoApp.MainWindow
            _library_form.Closed += _reset_form
        _library_form.Show()
        try:
            _library_form.BringToFront()
        except Exception:
            pass
        return True
    except Exception, exc:
        print("Errore apertura Libreria Interni: " + str(exc))
        raise


def RunCommand(is_interactive):
    OnLoadPlugIn()
    return 0


if __name__ == "__main__":
    OnLoadPlugIn()
