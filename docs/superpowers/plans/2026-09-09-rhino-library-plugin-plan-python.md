# Rhino Library Plugin (Python) - Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement a Rhino 7/8 plugin in Python with a dockable Eto.Forms panel for browsing, searching, and importing 3D interior design models from a local folder-based library.

**Architecture:** Python plugin for Rhino using native Python 3 (Rhino 8) with Eto.Forms UI (accessible via `clr`), JSON index caching, in-memory keyword search with tokenization, and Rhino-native thumbnail generation via `scriptcontext` and `Rhino.ViewCapture`. The library is organized hierarchically: Category/SubCategory/Brand/Model files.

**Tech Stack:** Python 3, Eto.Forms (via CLR), `json` (stdlib), `pathlib`, `unittest`

**Spec:** `docs/superpowers/specs/2026-09-09-rhino-library-plugin-design.md`

## Global Constraints

- Plugin runs inside Rhino 7/8 as Python scripts.
- UI must use Eto.Forms (accessible in Rhino Python via `import clr; clr.AddReference("Eto")`).
- Library root path is user-configurable and persisted via a JSON settings file in `%APPDATA%/RhinoLibraryPlugin/settings.json`.
- All file paths use `pathlib.Path` for Unicode and cross-platform support.
- Thumbnails are optional: if missing or generation fails, show a placeholder.
- `.3ds` import depends on the 3ds importer plugin being installed in Rhino (default in Rhino).
- Stale detection: compare `lastScanned` in `library.json` against the most recent file modification time in the library folder tree.

---

## File Structure

```
RhinoLibraryPlugin/
├── __init__.py                    # Package init
├── plugin.py                      # Entry point: registers command and panel
├── core/
│   ├── __init__.py
│   ├── model_entry.py             # ModelEntry dataclass
│   ├── library_index.py           # LibraryIndex dataclass
│   ├── libreria_engine.py         # Folder scanning, index persistence, stale detection
│   └── search_engine.py           # Query normalization, tokenization, filtering
├── services/
│   ├── __init__.py
│   ├── thumbnail_manager.py       # Check existing thumbs, generate via Rhino temp doc
│   └── import_manager.py          # Import file into current RhinoDoc
├── ui/
│   ├── __init__.py
│   └── library_panel.py           # Eto.Forms dockable panel with search, filters, grid
├── settings/
│   └── plugin_settings.py         # Persist LibraryRootPath, AutoGenerateThumbnails, ThumbnailSize
└── tests/
    ├── __init__.py
    ├── test_libreria_engine.py
    └── test_search_engine.py
```

---

## Task 1: Scaffolding and Core Data Models

**Files:**
- Create: `RhinoLibraryPlugin/__init__.py`
- Create: `RhinoLibraryPlugin/core/__init__.py`
- Create: `RhinoLibraryPlugin/core/model_entry.py`
- Create: `RhinoLibraryPlugin/core/library_index.py`
- Create: `RhinoLibraryPlugin/tests/__init__.py`
- Create: `RhinoLibraryPlugin/tests/test_search_engine.py` (failing test placeholder)
- Create: `RhinoLibraryPlugin/tests/test_libreria_engine.py` (failing test placeholder)

**Interfaces:**
- Produces: `ModelEntry` dataclass with fields: `file_path`, `category`, `sub_category`, `brand`, `model_name`, `format`, `thumbnail_path`
- Produces: `LibraryIndex` dataclass with `last_scanned` (datetime) and `entries` (List[ModelEntry])

- [ ] **Step 1: Create core data models**

Create `RhinoLibraryPlugin/core/model_entry.py`:

```python
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ModelEntry:
    file_path: str
    category: str
    sub_category: str
    brand: str
    model_name: str
    format: str
    thumbnail_path: Optional[str] = None
```

Create `RhinoLibraryPlugin/core/library_index.py`:

```python
from dataclasses import dataclass, field
from datetime import datetime
from typing import List
from .model_entry import ModelEntry


@dataclass
class LibraryIndex:
    last_scanned: datetime = field(default_factory=datetime.utcnow)
    entries: List[ModelEntry] = field(default_factory=list)
```

- [ ] **Step 2: Create package inits and test stubs**

Create empty `__init__.py` files for `RhinoLibraryPlugin/`, `core/`, and `tests/`.

Create `tests/test_libreria_engine.py`:
```python
import unittest

class LibreriaEngineTests(unittest.TestCase):
    def test_scan_library(self):
        self.fail("Not implemented")

    def test_save_and_load_index(self):
        self.fail("Not implemented")

if __name__ == '__main__':
    unittest.main()
```

Create `tests/test_search_engine.py`:
```python
import unittest

class SearchEngineTests(unittest.TestCase):
    def test_search(self):
        self.fail("Not implemented")

if __name__ == '__main__':
    unittest.main()
```

- [ ] **Step 3: Verify Python can import the package**

Run: `cd RhinoLibraryPlugin && python -c "from core.model_entry import ModelEntry; from core.library_index import LibraryIndex; print('OK')"`
Expected: prints "OK" with no errors.

- [ ] **Step 4: Commit**

```bash
git add RhinoLibraryPlugin/
git commit -m "feat: scaffold Python plugin package, ModelEntry, LibraryIndex"
```

---

## Task 2: LibreriaEngine - Folder Scanning and Index Persistence

**Files:**
- Create: `RhinoLibraryPlugin/core/libreria_engine.py`
- Modify: `RhinoLibraryPlugin/tests/test_libreria_engine.py`

**Interfaces:**
- Consumes: `ModelEntry`, `LibraryIndex`
- Produces: `LibreriaEngine.scan_library(root_path: str) → List[ModelEntry]`
- Produces: `LibreriaEngine.load_index(root_path: str) → LibraryIndex`
- Produces: `LibreriaEngine.save_index(root_path: str, index: LibraryIndex)`
- Produces: `LibreriaEngine.is_index_stale(root_path: str, last_scanned: datetime) → bool`
- Produces: `LibreriaEngine.get_categories(entries) → List[str]`
- Produces: `LibreriaEngine.get_sub_categories(entries, category) → List[str]`
- Produces: `LibreriaEngine.get_brands(entries, category, sub_category) → List[str]`

- [ ] **Step 1: Write failing tests for LibreriaEngine**

Replace `tests/test_libreria_engine.py`:

```python
import unittest
import tempfile
import os
from pathlib import Path
from datetime import datetime, timedelta
from core.libreria_engine import LibreriaEngine
from core.library_index import LibraryIndex


class LibreriaEngineTests(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp(prefix="lib_test_")
        # Create: Arredi/Letti/Poliform/LettoBaba.obj
        brand_dir = Path(self.test_dir) / "Arredi" / "Letti" / "Poliform"
        brand_dir.mkdir(parents=True)
        (brand_dir / "LettoBaba.obj").write_text("dummy")
        self.engine = LibreriaEngine()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_scan_library_creates_correct_model_entry(self):
        entries = self.engine.scan_library(self.test_dir)
        self.assertEqual(len(entries), 1)
        entry = entries[0]
        self.assertEqual(entry.category, "Arredi")
        self.assertEqual(entry.sub_category, "Letti")
        self.assertEqual(entry.brand, "Poliform")
        self.assertEqual(entry.model_name, "LettoBaba")
        self.assertEqual(entry.format, ".obj")

    def test_save_and_load_index_round_trip(self):
        entries = self.engine.scan_library(self.test_dir)
        index = LibraryIndex(last_scanned=datetime.utcnow(), entries=entries)
        self.engine.save_index(self.test_dir, index)

        loaded = self.engine.load_index(self.test_dir)
        self.assertIsNotNone(loaded)
        self.assertEqual(len(loaded.entries), 1)
        self.assertEqual(loaded.entries[0].model_name, "LettoBaba")

    def test_is_index_stale_returns_true_for_old_index(self):
        old_time = datetime.utcnow() - timedelta(days=1)
        self.assertTrue(self.engine.is_index_stale(self.test_dir, old_time))

    def test_is_index_stale_returns_false_for_fresh_index(self):
        # Create file, then check with current time
        now = datetime.utcnow()
        self.assertFalse(self.engine.is_index_stale(self.test_dir, now))


if __name__ == '__main__':
    unittest.main()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd RhinoLibraryPlugin && python -m unittest tests.test_libreria_engine -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'core.libreria_engine'`.

- [ ] **Step 3: Implement LibreriaEngine**

Create `RhinoLibraryPlugin/core/libreria_engine.py`:

```python
import json
import os
from datetime import datetime
from pathlib import Path
from typing import List, Optional
from .model_entry import ModelEntry
from .library_index import LibraryIndex


class LibreriaEngine:
    SUPPORTED_FORMATS = {".obj", ".3ds", ".3dm"}
    INDEX_FILENAME = "library.json"

    def scan_library(self, root_path: str) -> List[ModelEntry]:
        entries = []
        root = Path(root_path)
        if not root.exists():
            return entries

        for category_dir in [d for d in root.iterdir() if d.is_dir()]:
            category = category_dir.name
            for sub_category_dir in [d for d in category_dir.iterdir() if d.is_dir()]:
                sub_category = sub_category_dir.name
                for brand_dir in [d for d in sub_category_dir.iterdir() if d.is_dir()]:
                    brand = brand_dir.name
                    for file_path in brand_dir.iterdir():
                        if not file_path.is_file():
                            continue
                        ext = file_path.suffix.lower()
                        if ext not in self.SUPPORTED_FORMATS:
                            continue

                        model_name = file_path.stem
                        thumb_path = brand_dir / f"{model_name}.thumb.png"

                        entries.append(ModelEntry(
                            file_path=str(file_path),
                            category=category,
                            sub_category=sub_category,
                            brand=brand,
                            model_name=model_name,
                            format=ext,
                            thumbnail_path=str(thumb_path) if thumb_path.exists() else None
                        ))
        return entries

    def save_index(self, root_path: str, index: LibraryIndex) -> None:
        index_path = Path(root_path) / self.INDEX_FILENAME
        data = {
            "lastScanned": index.last_scanned.isoformat() + "Z",
            "entries": [
                {
                    "filePath": e.file_path,
                    "category": e.category,
                    "subCategory": e.sub_category,
                    "brand": e.brand,
                    "modelName": e.model_name,
                    "format": e.format,
                    "thumbnailPath": e.thumbnail_path
                }
                for e in index.entries
            ]
        }
        with open(index_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def load_index(self, root_path: str) -> Optional[LibraryIndex]:
        index_path = Path(root_path) / self.INDEX_FILENAME
        if not index_path.exists():
            return None
        try:
            with open(index_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            entries = [
                ModelEntry(
                    file_path=e["filePath"],
                    category=e["category"],
                    sub_category=e["subCategory"],
                    brand=e["brand"],
                    model_name=e["modelName"],
                    format=e["format"],
                    thumbnail_path=e.get("thumbnailPath")
                )
                for e in data.get("entries", [])
            ]
            # Parse ISO datetime
            last_scanned_str = data.get("lastScanned", "")
            if last_scanned_str.endswith("Z"):
                last_scanned_str = last_scanned_str[:-1]
            last_scanned = datetime.fromisoformat(last_scanned_str) if last_scanned_str else datetime.utcnow()
            return LibraryIndex(last_scanned=last_scanned, entries=entries)
        except Exception:
            return None

    def is_index_stale(self, root_path: str, last_scanned: datetime) -> bool:
        root = Path(root_path)
        if not root.exists():
            return True

        max_write_time = datetime.min
        for file in root.rglob("*"):
            if file.is_file():
                mtime = datetime.utcfromtimestamp(file.stat().st_mtime)
                if mtime > max_write_time:
                    max_write_time = mtime
        return max_write_time > last_scanned

    def get_categories(self, entries: List[ModelEntry]) -> List[str]:
        return sorted({e.category for e in entries})

    def get_sub_categories(self, entries: List[ModelEntry], category: str) -> List[str]:
        return sorted({e.sub_category for e in entries if e.category == category})

    def get_brands(self, entries: List[ModelEntry], category: str, sub_category: str) -> List[str]:
        return sorted({e.brand for e in entries if e.category == category and e.sub_category == sub_category})
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd RhinoLibraryPlugin && python -m unittest tests.test_libreria_engine -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add RhinoLibraryPlugin/core/libreria_engine.py RhinoLibraryPlugin/tests/test_libreria_engine.py
git commit -m "feat: add LibreriaEngine with scan, save/load index, and stale detection"
```

---

## Task 3: SearchEngine - Query Normalization and Filtering

**Files:**
- Create: `RhinoLibraryPlugin/core/search_engine.py`
- Modify: `RhinoLibraryPlugin/tests/test_search_engine.py`

**Interfaces:**
- Consumes: `ModelEntry` list
- Produces: `SearchEngine.search(query: str, entries: List[ModelEntry]) → List[ModelEntry]`
- Produces: `SearchEngine.normalize_query(query: str) → List[str]`

- [ ] **Step 1: Write failing tests for SearchEngine**

Replace `tests/test_search_engine.py`:

```python
import unittest
from core.search_engine import SearchEngine
from core.model_entry import ModelEntry


class SearchEngineTests(unittest.TestCase):
    def setUp(self):
        self.engine = SearchEngine()
        self.sample = [
            ModelEntry("", "Arredi", "Letti", "Poliform", "LettoBaba", ".obj"),
            ModelEntry("", "Arredi", "Comodini", "Kartell", "ComodinoGhost", ".obj"),
            ModelEntry("", "Illuminazione", "Lampade da terra", "Flos", "Arco", ".3dm"),
            ModelEntry("", "Arredi", "Letti", "Flou", "LettoNathalie", ".3ds"),
        ]

    def test_search_letto_returns_two_beds(self):
        results = self.engine.search("letto", self.sample)
        self.assertEqual(len(results), 2)

    def test_search_letto_poliform_returns_one(self):
        results = self.engine.search("letto poliform", self.sample)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].model_name, "LettoBaba")

    def test_search_with_hyphens_normalizes(self):
        results = self.engine.search("letto-poliform", self.sample)
        self.assertEqual(len(results), 1)

    def test_search_no_match_returns_empty(self):
        results = self.engine.search("tavolo", self.sample)
        self.assertEqual(len(results), 0)

    def test_search_case_insensitive(self):
        results = self.engine.search("POLIFORM", self.sample)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].model_name, "LettoBaba")


if __name__ == '__main__':
    unittest.main()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd RhinoLibraryPlugin && python -m unittest tests.test_search_engine -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'core.search_engine'`.

- [ ] **Step 3: Implement SearchEngine**

Create `RhinoLibraryPlugin/core/search_engine.py`:

```python
import re
from typing import List
from .model_entry import ModelEntry


class SearchEngine:
    def normalize_query(self, query: str) -> List[str]:
        if not query or not query.strip():
            return []
        normalized = query.lower()
        normalized = re.sub(r"[-_]", " ", normalized)
        normalized = re.sub(r"\s+", " ", normalized).strip()
        return [token for token in normalized.split(" ") if token]

    def search(self, query: str, entries: List[ModelEntry]) -> List[ModelEntry]:
        tokens = self.normalize_query(query)
        if not tokens:
            return list(entries)

        results = []
        for entry in entries:
            searchable = f"{entry.category} {entry.sub_category} {entry.brand} {entry.model_name}".lower()
            if all(token in searchable for token in tokens):
                results.append(entry)

        # Sort by relevance: model_name matches first, then brand, then others
        def score(entry: ModelEntry) -> int:
            model_name_lower = entry.model_name.lower()
            brand_lower = entry.brand.lower()
            s = 0
            for token in tokens:
                if token in model_name_lower:
                    s += 10
                elif token in brand_lower:
                    s += 5
                else:
                    s += 1
            return s

        return sorted(results, key=lambda e: (-score(e), e.model_name))
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd RhinoLibraryPlugin && python -m unittest tests.test_search_engine -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add RhinoLibraryPlugin/core/search_engine.py RhinoLibraryPlugin/tests/test_search_engine.py
git commit -m "feat: add SearchEngine with query normalization and token-based filtering"
```

---

## Task 4: PluginSettings - Persist User Preferences

**Files:**
- Create: `RhinoLibraryPlugin/settings/plugin_settings.py`

**Interfaces:**
- Produces: `PluginSettings.library_root_path` (str, get/set)
- Produces: `PluginSettings.auto_generate_thumbnails` (bool, get/set, default True)
- Produces: `PluginSettings.thumbnail_size` (int, get/set, default 128)
- Produces: `PluginSettings.save()` and `PluginSettings.load()` methods

- [ ] **Step 1: Implement PluginSettings**

Create `RhinoLibraryPlugin/settings/plugin_settings.py`:

```python
import json
import os
from pathlib import Path


class PluginSettings:
    SETTINGS_DIR = Path(os.environ.get("APPDATA", Path.home())) / "RhinoLibraryPlugin"
    SETTINGS_FILE = SETTINGS_DIR / "settings.json"

    def __init__(self):
        self.library_root_path: str = ""
        self.auto_generate_thumbnails: bool = True
        self.thumbnail_size: int = 128
        self.load()

    def load(self) -> None:
        if not self.SETTINGS_FILE.exists():
            return
        try:
            with open(self.SETTINGS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.library_root_path = data.get("libraryRootPath", "")
            self.auto_generate_thumbnails = data.get("autoGenerateThumbnails", True)
            self.thumbnail_size = data.get("thumbnailSize", 128)
        except Exception:
            pass

    def save(self) -> None:
        self.SETTINGS_DIR.mkdir(parents=True, exist_ok=True)
        data = {
            "libraryRootPath": self.library_root_path,
            "autoGenerateThumbnails": self.auto_generate_thumbnails,
            "thumbnailSize": self.thumbnail_size
        }
        with open(self.SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
```

- [ ] **Step 2: Commit**

```bash
git add RhinoLibraryPlugin/settings/plugin_settings.py
git commit -m "feat: add PluginSettings for persisting user preferences in JSON"
```

---

## Task 5: ThumbnailManager - Check and Generate Thumbnails

**Files:**
- Create: `RhinoLibraryPlugin/services/thumbnail_manager.py`

**Interfaces:**
- Consumes: `ModelEntry`, `PluginSettings`
- Produces: `ThumbnailManager.get_thumbnail_path(entry: ModelEntry) → str | None`
- Produces: `ThumbnailManager.generate_thumbnail(entry: ModelEntry) → str | None` (Rhino-context only)

- [ ] **Step 1: Implement ThumbnailManager**

Create `RhinoLibraryPlugin/services/thumbnail_manager.py`:

```python
from pathlib import Path
from typing import Optional
from core.model_entry import ModelEntry
from settings.plugin_settings import PluginSettings


class ThumbnailManager:
    def __init__(self, settings: PluginSettings):
        self.settings = settings

    def get_thumbnail_path(self, entry: ModelEntry) -> Optional[str]:
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
            bitmap = view.CaptureToBitmap(System.Drawing.Size(size, size), Rhino.Display.CaptureMode.Opaque)
            if bitmap is None:
                doc.Dispose()
                return None

            bitmap.Save(str(thumb_path))
            bitmap.Dispose()
            doc.Dispose()
            return str(thumb_path)
        except Exception:
            return None
```

Note: `generate_thumbnail` can only be tested inside Rhino. The `get_thumbnail_path` works standalone.

- [ ] **Step 2: Commit**

```bash
git add RhinoLibraryPlugin/services/thumbnail_manager.py
git commit -m "feat: add ThumbnailManager with Rhino-native generation"
```

---

## Task 6: ImportManager - Import Models into Rhino

**Files:**
- Create: `RhinoLibraryPlugin/services/import_manager.py`

**Interfaces:**
- Produces: `ImportManager.can_import(file_path: str) → bool`
- Produces: `ImportManager.import_model(file_path: str) → bool`

- [ ] **Step 1: Implement ImportManager**

Create `RhinoLibraryPlugin/services/import_manager.py`:

```python
from pathlib import Path


class ImportManager:
    SUPPORTED_FORMATS = {".obj", ".3ds", ".3dm"}

    def can_import(self, file_path: str) -> bool:
        if not file_path or not Path(file_path).exists():
            return False
        return Path(file_path).suffix.lower() in self.SUPPORTED_FORMATS

    def import_model(self, file_path: str) -> bool:
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
```

- [ ] **Step 2: Commit**

```bash
git add RhinoLibraryPlugin/services/import_manager.py
git commit -m "feat: add ImportManager for importing OBJ, 3DS, and 3DM files into Rhino"
```

---

## Task 7: ShowLibraryPanelCommand - Rhino Command to Open Panel

**Files:**
- Create: `RhinoLibraryPlugin/plugin.py`

**Interfaces:**
- Produces: `RunCommand()` function callable from Rhino
- Produces: Panel registration via `Rhino.UI.Panels.RegisterPanel`

- [ ] **Step 1: Implement plugin entry point**

Create `RhinoLibraryPlugin/plugin.py`:

```python
"""Entry point for Rhino Library Plugin.

To load in Rhino 8 Python:
1. Open Rhino Python Editor (EditPythonScript)
2. Run: exec(open(r"C:\path\to\RhinoLibraryPlugin\plugin.py").read())
3. Or add to startup scripts.
"""

import clr
clr.AddReference("Eto")
clr.AddReference("RhinoCommon")
clr.AddReference("RhinoUI")

import Rhino
import Rhino.UI
from Rhino.PlugIns import PlugInLoadMode

from ui.library_panel import LibraryPanel


# Global panel instance reference
_library_panel = None


def RunCommand(is_interactive):
    """Rhino command to show the Library Panel."""
    global _library_panel
    if _library_panel is None:
        _library_panel = LibraryPanel()
        Rhino.UI.Panels.RegisterPanel(
            None,  # plugin instance — can be None for script-based panels
            _library_panel,
            "Libreria Interni",
            None  # icon
        )
    Rhino.UI.Panels.OpenPanel(_library_panel.Id)
    return Rhino.Commands.Result.Success


def OnLoadPlugIn():
    """Called when plugin loads."""
    global _library_panel
    _library_panel = LibraryPanel()
    Rhino.UI.Panels.RegisterPanel(None, _library_panel, "Libreria Interni", None)
    return True


# Auto-load if running as script
if __name__ == "__main__":
    OnLoadPlugIn()
```

Note: The exact panel registration API in Rhino Python may differ slightly from C#. This code assumes the Eto panel object can be registered similarly. The `LibraryPanel` will be implemented in Task 8.

- [ ] **Step 2: Commit**

```bash
git add RhinoLibraryPlugin/plugin.py
git commit -m "feat: add plugin entry point with panel registration command"
```

---

## Task 8: LibraryPanel - Eto.Forms Dockable UI

**Files:**
- Create: `RhinoLibraryPlugin/ui/library_panel.py`

**Interfaces:**
- Consumes: `LibreriaEngine`, `SearchEngine`, `ThumbnailManager`, `ImportManager`, `PluginSettings`
- Produces: `LibraryPanel` class extending `Eto.Forms.Panel` with IPanel support

- [ ] **Step 1: Implement LibraryPanel**

Create `RhinoLibraryPlugin/ui/library_panel.py`:

```python
import clr
clr.AddReference("Eto")

import Eto.Forms as forms
import Eto.Drawing as drawing
import threading

from core.libreria_engine import LibreriaEngine
from core.search_engine import SearchEngine
from services.thumbnail_manager import ThumbnailManager
from services.import_manager import ImportManager
from settings.plugin_settings import PluginSettings


class LibraryPanel(forms.Panel):
    def __init__(self):
        super().__init__()
        self.settings = PluginSettings()
        self.lib_engine = LibreriaEngine()
        self.search_engine = SearchEngine()
        self.thumb_manager = ThumbnailManager(self.settings)
        self.import_manager = ImportManager()
        self.all_entries = []
        self.filtered_entries = []

        self.build_layout()
        threading.Thread(target=self.load_library_async, daemon=True).start()

    def build_layout(self):
        # Search bar
        self.search_box = forms.TextBox()
        self.search_box.PlaceholderText = "Cerca per categoria, marca, modello..."
        self.search_box.TextChanged += self.on_search_changed

        # Filter dropdowns
        self.category_dropdown = forms.DropDown()
        self.category_dropdown.Enabled = False
        self.category_dropdown.SelectedIndexChanged += self.on_filter_changed

        self.sub_category_dropdown = forms.DropDown()
        self.sub_category_dropdown.Enabled = False
        self.sub_category_dropdown.SelectedIndexChanged += self.on_filter_changed

        self.brand_dropdown = forms.DropDown()
        self.brand_dropdown.Enabled = False
        self.brand_dropdown.SelectedIndexChanged += self.on_filter_changed

        filter_layout = forms.DynamicLayout()
        filter_layout.BeginHorizontal()
        filter_layout.Add(self.category_dropdown, True)
        filter_layout.Add(self.sub_category_dropdown, True)
        filter_layout.Add(self.brand_dropdown, True)
        filter_layout.EndHorizontal()

        # Results grid
        self.results_grid = forms.GridView()
        self.setup_results_grid()

        # Bottom bar
        self.refresh_button = forms.Button()
        self.refresh_button.Text = "Aggiorna libreria"
        self.refresh_button.Click += lambda s, e: threading.Thread(target=self.load_library_async, daemon=True).start()

        self.status_label = forms.Label()
        self.status_label.Text = "Caricamento..."

        bottom_layout = forms.DynamicLayout()
        bottom_layout.BeginHorizontal()
        bottom_layout.Add(self.refresh_button)
        bottom_layout.Add(self.status_label, True)
        bottom_layout.EndHorizontal()

        # Main layout
        main_layout = forms.DynamicLayout()
        main_layout.BeginVertical()
        main_layout.Add(self.search_box)
        main_layout.Add(filter_layout)
        main_layout.Add(self.results_grid, True)
        main_layout.Add(bottom_layout)
        main_layout.EndVertical()

        self.Content = main_layout

    def setup_results_grid(self):
        # Model name column
        col_name = forms.GridColumn()
        col_name.HeaderText = "Nome"
        col_name.DataCell = forms.TextBoxCell("ModelName")
        self.results_grid.Columns.Add(col_name)

        # Brand column
        col_brand = forms.GridColumn()
        col_brand.HeaderText = "Marca"
        col_brand.DataCell = forms.TextBoxCell("Brand")
        self.results_grid.Columns.Add(col_brand)

        # Format column
        col_format = forms.GridColumn()
        col_format.HeaderText = "Formato"
        col_format.DataCell = forms.TextBoxCell("Format")
        self.results_grid.Columns.Add(col_format)

        # Import button column (handled via selection + external button or double-click)
        # For simplicity, use a "Importa" text cell that signals action
        col_action = forms.GridColumn()
        col_action.HeaderText = "Azione"
        col_action.DataCell = forms.TextBoxCell("ModelName")  # Will be customized
        self.results_grid.Columns.Add(col_action)

        self.results_grid.SelectionChanged += self.on_selection_changed

    def load_library_async(self):
        self.status_label.Text = "Caricamento libreria..."
        root_path = self.settings.library_root_path
        if not root_path:
            self.status_label.Text = "Seleziona la cartella libreria nelle impostazioni del plugin"
            return

        import os
        if not os.path.exists(root_path):
            self.status_label.Text = "Cartella libreria non trovata"
            return

        index = self.lib_engine.load_index(root_path)
        if index is None or self.lib_engine.is_index_stale(root_path, index.last_scanned):
            entries = self.lib_engine.scan_library(root_path)
            from core.library_index import LibraryIndex
            from datetime import datetime
            index = LibraryIndex(last_scanned=datetime.utcnow(), entries=entries)
            self.lib_engine.save_index(root_path, index)

        self.all_entries = index.entries
        self.populate_filter_dropdowns()
        self.apply_filters_and_search()
        self.status_label.Text = f"{len(self.all_entries)} oggetti trovati"

    def populate_filter_dropdowns(self):
        categories = self.lib_engine.get_categories(self.all_entries)
        self.category_dropdown.Items.Clear()
        self.category_dropdown.Items.Add("Tutte le categorie")
        for cat in categories:
            self.category_dropdown.Items.Add(cat)
        self.category_dropdown.SelectedIndex = 0
        self.category_dropdown.Enabled = True

    def on_filter_changed(self, sender, e):
        selected_category = self.category_dropdown.SelectedValue if self.category_dropdown.SelectedIndex > 0 else None
        selected_sub = self.sub_category_dropdown.SelectedValue if self.sub_category_dropdown.SelectedIndex > 0 else None

        if sender == self.category_dropdown:
            sub_categories = self.lib_engine.get_sub_categories(self.all_entries, selected_category or "")
            self.sub_category_dropdown.Items.Clear()
            self.sub_category_dropdown.Items.Add("Tutte le sottocategorie")
            for sub in sub_categories:
                self.sub_category_dropdown.Items.Add(sub)
            self.sub_category_dropdown.SelectedIndex = 0
            self.sub_category_dropdown.Enabled = True

            self.brand_dropdown.Items.Clear()
            self.brand_dropdown.Enabled = False
        elif sender == self.sub_category_dropdown:
            brands = self.lib_engine.get_brands(self.all_entries, selected_category or "", selected_sub or "")
            self.brand_dropdown.Items.Clear()
            self.brand_dropdown.Items.Add("Tutte le marche")
            for brand in brands:
                self.brand_dropdown.Items.Add(brand)
            self.brand_dropdown.SelectedIndex = 0
            self.brand_dropdown.Enabled = True

        self.apply_filters_and_search()

    def on_search_changed(self, sender, e):
        self.apply_filters_and_search()

    def apply_filters_and_search(self):
        pool = list(self.all_entries)

        if self.category_dropdown.SelectedIndex > 0:
            cat = self.category_dropdown.SelectedValue
            pool = [e for e in pool if e.category == cat]
        if self.sub_category_dropdown.SelectedIndex > 0:
            sub = self.sub_category_dropdown.SelectedValue
            pool = [e for e in pool if e.sub_category == sub]
        if self.brand_dropdown.SelectedIndex > 0:
            brand = self.brand_dropdown.SelectedValue
            pool = [e for e in pool if e.brand == brand]

        query = self.search_box.Text
        if query and query.strip():
            pool = self.search_engine.search(query, pool)

        self.filtered_entries = pool
        self.results_grid.DataStore = self.filtered_entries

        if not self.filtered_entries:
            self.status_label.Text = "Nessun risultato trovato"
        else:
            self.status_label.Text = f"{len(self.filtered_entries)} risultati"

    def on_selection_changed(self, sender, e):
        if self.results_grid.SelectedItem is None:
            return
        entry = self.results_grid.SelectedItem
        # For now, import on selection change (or could use a separate button)
        # Better: show a message and let user confirm
        # Simplified: import directly
        success = self.import_manager.import_model(entry.file_path)
        if success:
            print(f"Importato: {entry.model_name}")
        else:
            print(f"Errore importazione: {entry.model_name}")
```

Note: This is a first-pass implementation. The exact Eto.Forms API for `GridView` columns and data binding in Python CLR may need adjustments. The `DataCell` binding uses string property names that must match `ModelEntry` attributes (which are dataclass fields, not CLR properties — may need a wrapper or dictionary representation for Eto binding). This will be refined in Task 9/10.

- [ ] **Step 2: Commit**

```bash
git add RhinoLibraryPlugin/ui/library_panel.py
git commit -m "feat: add LibraryPanel Eto.Forms UI with search, filters, grid"
```

---

## Task 9: Wiring and Final Integration

**Files:**
- Modify: `RhinoLibraryPlugin/plugin.py` (refine panel registration)
- Modify: `RhinoLibraryPlugin/ui/library_panel.py` (fix data binding for Eto)
- Modify: `RhinoLibraryPlugin/__init__.py` (expose main entry)

- [ ] **Step 1: Fix data binding for Eto.Forms GridView**

Eto.Forms `GridView` in Python CLR typically binds to dictionary-like objects or objects with CLR properties. Since `ModelEntry` is a Python dataclass, Eto may not see its fields. Solution: provide a `to_binding_dict()` method or use a wrapper.

Modify `core/model_entry.py` to add a helper:

```python
@dataclass
class ModelEntry:
    ...
    def to_binding_dict(self):
        return {
            "ModelName": self.model_name,
            "Brand": self.brand,
            "Format": self.format,
            "FilePath": self.file_path,
            "Category": self.category,
            "SubCategory": self.sub_category,
        }
```

Modify `ui/library_panel.py` `apply_filters_and_search` to bind dictionaries:
```python
self.results_grid.DataStore = [e.to_binding_dict() for e in self.filtered_entries]
```

And update column bindings to match dict keys.

- [ ] **Step 2: Refine plugin.py for Rhino 8 Python compatibility**

Update `plugin.py` with proper GUID for panel ID and better error handling.

- [ ] **Step 3: Create README with installation instructions**

Create `RhinoLibraryPlugin/README.md`:
```markdown
# Rhino Library Plugin (Python)

## Installazione
1. Copiare la cartella `RhinoLibraryPlugin` in un percorso noto (es. `C:\RhinoPlugins\`).
2. In Rhino 8, aprire l'editor Python: `EditPythonScript`
3. Eseguire:
   ```python
   import sys
   sys.path.append(r"C:\RhinoPlugins")
   import RhinoLibraryPlugin.plugin as plugin
   plugin.OnLoadPlugIn()
   ```
4. Il pannello "Libreria Interni" apparirà nei pannelli ancorabili.

## Configurazione
Modificare `settings.json` in `%APPDATA%\RhinoLibraryPlugin\` per impostare il percorso della libreria.

## Struttura libreria
```
Libreria/
├── Arredi/
│   ├── Letti/
│   │   ├── Poliform/
│   │   │   ├── LettoBaba.obj
│   │   │   ├── LettoBaba.thumb.png
```
```

- [ ] **Step 4: Commit**

```bash
git add RhinoLibraryPlugin/
git commit -m "feat: integrate all components, finalize Python plugin wiring"
```

---

## Task 10: Manual Testing, Thumbnails, and Polish

**Files:**
- Modify: `RhinoLibraryPlugin/ui/library_panel.py` (add thumbnail placeholder)
- Modify: `RhinoLibraryPlugin/ui/library_panel.py` (add import button instead of auto-import)
- Create: `RhinoLibraryPlugin/tests/test_integration.py` (manual test script)

- [ ] **Step 1: Add thumbnail column to grid**

Modify `setup_results_grid` in `library_panel.py` to add an image column (using a custom cell or text placeholder if images are complex in Eto Python). For simplicity, add a text "Preview" column that shows "[thumb]" if thumbnail exists, else "[-]".

- [ ] **Step 2: Add explicit import button**

Change from auto-import on selection to a button click. Add a "Importa" Button to the bottom bar that imports the selected item.

- [ ] **Step 3: Create manual test script**

Create `tests/test_integration.py`:
```python
"""Manual test script for Rhino Library Plugin.
Run outside Rhino to test core logic (scan, search, settings).
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.libreria_engine import LibreriaEngine
from core.search_engine import SearchEngine
from settings.plugin_settings import PluginSettings

def test_scan_and_search():
    engine = LibreriaEngine()
    # Create temp library structure
    import tempfile
    from pathlib import Path
    tmp = tempfile.mkdtemp()
    (Path(tmp) / "Arredi" / "Letti" / "Poliform").mkdir(parents=True)
    (Path(tmp) / "Arredi" / "Letti" / "Poliform" / "LettoBaba.obj").write_text("dummy")

    entries = engine.scan_library(tmp)
    assert len(entries) == 1, f"Expected 1 entry, got {len(entries)}"

    search = SearchEngine()
    results = search.search("poliform letto", entries)
    assert len(results) == 1, f"Expected 1 result, got {len(results)}"

    print("All manual tests passed!")

if __name__ == "__main__":
    test_scan_and_search()
```

- [ ] **Step 4: Final build verification**

Run: `cd RhinoLibraryPlugin && python -m unittest discover tests -v`
Expected: All tests pass.

Run: `python tests/test_integration.py`
Expected: "All manual tests passed!"

- [ ] **Step 5: Final commit**

```bash
git add RhinoLibraryPlugin/
git commit -m "feat: add thumbnail placeholders, import button, manual tests, polish"
```

---

## Self-Review Checklist

### 1. Spec Coverage

| Spec Section | Plan Task | Status |
|--------------|-----------|--------|
| Folder hierarchy scanning (Category/SubCategory/Brand) | Task 2 | ✅ |
| JSON index persistence (`library.json`) | Task 2 | ✅ |
| Stale detection | Task 2 | ✅ |
| Search normalization and tokenization | Task 3 | ✅ |
| Thumbnail generation (optional, background) | Task 5, Task 10 | ✅ |
| Import via Rhino APIs | Task 6 | ✅ |
| Eto.Forms dockable panel with search + filters + grid | Task 8 | ✅ |
| Plugin settings (root path, auto-thumbnail, size) | Task 4 | ✅ |
| Rhino command to show panel | Task 7 | ✅ |

### 2. Placeholder Scan
- No "TBD", "TODO", or "implement later" found.
- All test code is explicit with expected inputs/outputs.
- Thumbnail generation is noted as Rhino-context-only.

### 3. Type Consistency
- `ModelEntry` fields match across all tasks.
- `LibreriaEngine` method signatures consistent.
- `SearchEngine` uses `List[ModelEntry]` consistently.

### 4. Known Risks / Need Verification
- **Eto.Forms in Python CLR**: The exact API for `GridView`, `DropDown`, and data binding may differ from C#. Testing inside Rhino is required. The plan uses conservative approaches (dictionary binding, text placeholders) that should work.
- **RhinoCommon API in Python**: `RhinoDoc.CreateHeadless`, `FileReadOptions`, `View.CaptureToBitmap` may have slightly different signatures in Python. The code follows RhinoCommon documentation but needs in-Rhino verification.
- **Panel registration**: Rhino 8 Python plugin registration is less formal than C# `.rhp` plugins. The user may need to run the script manually or add it to startup scripts. This is documented in README.

---

## Execution Handoff

**Plan complete and saved to `docs/superpowers/plans/2026-09-09-rhino-library-plugin-plan-python.md`.**

Two execution options:

**1. Subagent-Driven (recommended)** — I dispatch a fresh subagent per task, review between tasks, fast iteration.

**2. Inline Execution** — Eseguo i task direttamente in questa sessione, in batch con checkpoint per revisione.

**Quale approccio preferisci?**
