#! python 3
"""Smoke test da eseguire DENTRO Rhino 8 (Python 3).

Verifica il punto 1 di docs/handoff.md:
- caricamento plugin / pannello
- dropdown filtri
- ricerca testuale
- import nel documento
"""
from __future__ import print_function

import json
import os
import sys
import time
import traceback
from pathlib import Path

PLUGIN_DIR = Path(__file__).resolve().parents[1]
WORKSPACE = PLUGIN_DIR.parent
FIXTURE_LIB = PLUGIN_DIR / "tests" / "fixtures" / "libreria"
REPORT_PATH = PLUGIN_DIR / "tests" / "rhino_smoke_report.json"

sys.path.insert(0, str(PLUGIN_DIR))
sys.path.insert(0, str(WORKSPACE))

results = []


def record(name, ok, detail=""):
    results.append({"name": name, "ok": bool(ok), "detail": str(detail)[:4000]})
    print("[{}] {} {}".format("PASS" if ok else "FAIL", name, detail))


def write_report():
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "all_ok": all(r["ok"] for r in results) if results else False,
        "results": results,
    }
    REPORT_PATH.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print("Report scritto in {}".format(REPORT_PATH))


def prepare_settings():
    from settings.plugin_settings import PluginSettings

    settings = PluginSettings()
    settings.library_root_path = str(FIXTURE_LIB)
    settings.auto_generate_thumbnails = False
    settings.save()
    record("settings_scritti", True, settings.library_root_path)


def test_register_panel():
    from plugin import OnLoadPlugIn, RunCommand

    try:
        ok = OnLoadPlugIn()
        record("OnLoadPlugIn", True, "return={}".format(ok))
    except Exception:
        record("OnLoadPlugIn", False, traceback.format_exc())

    try:
        result = RunCommand(True)
        record("RunCommand", True, "return={}".format(result))
    except Exception:
        record("RunCommand", False, traceback.format_exc())


def wait_for_entries(panel, timeout=8.0):
    deadline = time.time() + timeout
    while time.time() < deadline:
        if getattr(panel, "all_entries", None):
            return True
        time.sleep(0.2)
    return bool(getattr(panel, "all_entries", None))


def test_panel_filters_search_import():
    import Rhino
    from ui.library_panel import LibraryPanel
    from services.import_manager import ImportManager

    try:
        panel = LibraryPanel()
        record("LibraryPanel_ctor", True)
    except Exception:
        record("LibraryPanel_ctor", False, traceback.format_exc())
        return

    loaded = wait_for_entries(panel)
    status = getattr(getattr(panel, "status_label", None), "Text", "")
    n = len(getattr(panel, "all_entries", []) or [])
    record("caricamento_libreria", loaded and n >= 2, "entries={} status={}".format(n, status))

    try:
        cats = list(panel.category_dropdown.Items)
        cat_ok = panel.category_dropdown.Enabled and len(cats) >= 2
        record("dropdown_categorie", cat_ok, "items={}".format([str(x) for x in cats]))
    except Exception:
        record("dropdown_categorie", False, traceback.format_exc())

    try:
        # Simula scelta categoria Arredi
        items = [str(x) for x in panel.category_dropdown.Items]
        if "Arredi" in items:
            panel.category_dropdown.SelectedIndex = items.index("Arredi")
            panel.on_filter_changed(panel.category_dropdown, None)
        subs = [str(x) for x in panel.sub_category_dropdown.Items]
        sub_ok = panel.sub_category_dropdown.Enabled and any("Letti" in s for s in subs)
        record("dropdown_sottocategorie", sub_ok, "items={}".format(subs))
    except Exception:
        record("dropdown_sottocategorie", False, traceback.format_exc())

    try:
        panel.search_box.Text = "poliform letto"
        panel.on_search_changed(panel.search_box, None)
        names = [e.model_name for e in panel.filtered_entries]
        record("ricerca_testuale", names == ["LettoBaba"], "results={}".format(names))
    except Exception:
        record("ricerca_testuale", False, traceback.format_exc())

    try:
        store = panel.results_grid.DataStore
        store_len = len(list(store)) if store is not None else 0
        record("grid_datastore", store_len >= 1, "rows={}".format(store_len))
    except Exception:
        record("grid_datastore", False, traceback.format_exc())

    try:
        doc = Rhino.RhinoDoc.ActiveDoc
        before = doc.Objects.Count if doc else -1
        importer = ImportManager()
        model_path = str(FIXTURE_LIB / "Arredi" / "Letti" / "Poliform" / "LettoBaba.obj")
        success = importer.import_model(model_path)
        after = doc.Objects.Count if doc else -1
        record(
            "import_selezionato",
            bool(success) and after > before,
            "success={} objects {} -> {}".format(success, before, after),
        )
    except Exception:
        record("import_selezionato", False, traceback.format_exc())


def try_show_modeless_form():
    """Se RegisterPanel non e' disponibile da Python, verifica comunque l'UI Eto."""
    try:
        import Eto.Forms as forms
        from ui.library_panel import LibraryPanel

        panel = LibraryPanel()
        form = forms.Form()
        form.Title = "Libreria Interni (smoke test)"
        form.ClientSize = __import__("Eto.Drawing", fromlist=["Size"]).Size(420, 520)
        form.Content = panel
        form.Owner = __import__("Rhino.UI", fromlist=["RhinoEtoApp"]).RhinoEtoApp.MainWindow
        form.Show()
        record("form_modeless", True, "form mostrata (workaround se il pannello ancorabile non e' registrabile da Python)")
        form.Close()
    except Exception:
        record("form_modeless", False, traceback.format_exc())


def close_rhino():
    try:
        import Rhino

        doc = Rhino.RhinoDoc.ActiveDoc
        if doc is not None:
            doc.Modified = False
        Rhino.RhinoApp.InvokeOnUiThread(lambda: Rhino.RhinoApp.RunScript("_-Exit No", False))
        record("exit_rhino", True)
    except Exception:
        record("exit_rhino", False, traceback.format_exc())


def main():
    try:
        prepare_settings()
        test_register_panel()
        test_panel_filters_search_import()
        try_show_modeless_form()
    except Exception:
        record("smoke_test_crash", False, traceback.format_exc())
    finally:
        write_report()
        close_rhino()


if __name__ == "__main__":
    main()
else:
    main()
