"""Entry point for Rhino Library Plugin (IronPython 2 / Rhino 7 e 8)."""
import clr

clr.AddReference("Eto")
clr.AddReference("RhinoCommon")

import Eto.Drawing as drawing
import Eto.Forms as forms
import Rhino.UI

from ui.library_panel import LibraryPanel

_library_form = None
_gimmemore_form = None


def _setup_host_form(form):
    form.ClientSize = drawing.Size(560, 380)
    form.MinimumSize = drawing.Size(420, 260)
    form.Padding = drawing.Padding(6)
    form.Resizable = True
    form.Maximizable = True
    form.ShowInTaskbar = False
    form.Topmost = False


class LibraryHostForm(forms.Form):
    def __init__(self):
        super(LibraryHostForm, self).__init__()
        self.Title = "Libreria Interni (cartella)"
        _setup_host_form(self)
        self.Content = LibraryPanel()


class GimmeMoreHostForm(forms.Form):
    def __init__(self):
        super(GimmeMoreHostForm, self).__init__()
        self.Title = "GimmeMore"
        _setup_host_form(self)
        LibraryPanel._create_pose_mode = True
        panel = LibraryPanel()
        self.Content = panel
        panel.host_form = self


def _reset_form(sender, e):
    global _library_form
    _library_form = None


def _reset_gimmemore_form(sender, e):
    global _gimmemore_form
    _gimmemore_form = None


def OnLoadPlugIn():
    global _library_form
    try:
        if _library_form is None:
            _library_form = LibraryHostForm()
            try:
                _library_form.Owner = Rhino.UI.RhinoEtoApp.MainWindow
            except Exception:
                pass
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


def OnLoadGimmeMore():
    global _gimmemore_form
    try:
        if _gimmemore_form is None:
            _gimmemore_form = GimmeMoreHostForm()
            try:
                _gimmemore_form.Owner = Rhino.UI.RhinoEtoApp.MainWindow
            except Exception:
                pass
            _gimmemore_form.Closed += _reset_gimmemore_form
        _gimmemore_form.Show()
        try:
            _gimmemore_form.BringToFront()
        except Exception:
            pass
        return True
    except Exception, exc:
        print("Errore apertura GimmeMore: " + str(exc))
        raise


def RunCommand(is_interactive):
    OnLoadPlugIn()
    return 0


if __name__ == "__main__":
    OnLoadPlugIn()
