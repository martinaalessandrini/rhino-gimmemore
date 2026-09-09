"""Manual test script for Rhino Library Plugin core logic.
Run outside Rhino to test scanning, indexing, search, and settings.
"""
import sys
import os
import tempfile
import shutil
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.libreria_engine import LibreriaEngine
from core.search_engine import SearchEngine
from core.library_index import LibraryIndex
from settings.plugin_settings import PluginSettings


def test_scan_and_search():
    engine = LibreriaEngine()
    # Create temp library structure
    tmp = tempfile.mkdtemp()
    (Path(tmp) / "Arredi" / "Letti" / "Poliform").mkdir(parents=True)
    (Path(tmp) / "Arredi" / "Letti" / "Flou").mkdir(parents=True)
    (Path(tmp) / "Arredi" / "Letti" / "Poliform" / "LettoBaba.obj").write_text("dummy")
    (Path(tmp) / "Arredi" / "Letti" / "Flou" / "LettoNathalie.3ds").write_text("dummy")
    (Path(tmp) / "Arredi" / "Letti" / "Poliform" / "LettoBaba.thumb.png").write_text("dummy_thumb")

    # Test scan
    entries = engine.scan_library(tmp)
    assert len(entries) == 2, f"Expected 2 entries, got {len(entries)}"
    poliform_entry = next(e for e in entries if e.model_name == "LettoBaba")
    assert poliform_entry.thumbnail_path is not None, "Thumbnail path should be detected"

    # Test index save/load
    index = LibraryIndex(entries=entries)
    engine.save_index(tmp, index)
    loaded = engine.load_index(tmp)
    assert loaded is not None, "Index should load"
    assert len(loaded.entries) == 2, f"Expected 2 loaded entries, got {len(loaded.entries)}"

    # Test search
    search = SearchEngine()
    results = search.search("poliform letto", entries)
    assert len(results) == 1, f"Expected 1 result, got {len(results)}"
    assert results[0].model_name == "LettoBaba", f"Expected LettoBaba, got {results[0].model_name}"

    # Test settings
    settings = PluginSettings()
    settings.library_root_path = tmp
    settings.save()
    settings2 = PluginSettings()
    assert settings2.library_root_path == tmp, "Settings should persist"

    # Cleanup
    shutil.rmtree(tmp)
    # Clean settings file
    settings_file = PluginSettings.SETTINGS_FILE
    if settings_file.exists():
        settings_file.unlink()

    print("All manual integration tests passed!")


if __name__ == "__main__":
    test_scan_and_search()
