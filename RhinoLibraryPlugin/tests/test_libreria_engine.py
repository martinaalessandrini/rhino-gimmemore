import unittest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime, timedelta
import sys
import os

# Add parent dir to path so we can import the package
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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
        later = datetime.utcnow() + timedelta(seconds=5)
        self.assertFalse(self.engine.is_index_stale(self.test_dir, later))

    def test_scan_finds_models_nested_inside_brand_folders(self):
        lago = Path(self.test_dir) / "Arredi" / "Letti" / "LAGO" / "LAGO Fluttua 180x200"
        lago.mkdir(parents=True)
        (lago / "LAGO_WEB_FLUVU.obj").write_text("dummy")
        pianca = (
            Path(self.test_dir) / "Arredi" / "Letti" / "Pianca" /
            "Pianca - Bricola" / "19_BRICOLA" / "01_LETTI" / "OBJ"
        )
        pianca.mkdir(parents=True)
        (pianca / "WBCB13C.obj").write_text("dummy")
        macosx = Path(self.test_dir) / "Arredi" / "Letti" / "Twils" / "opera" / "__MACOSX"
        macosx.mkdir(parents=True)
        (macosx / "._Opera.obj").write_text("junk")

        entries = self.engine.scan_library(self.test_dir)
        brands = sorted(set([e.brand for e in entries]))
        names = sorted([e.model_name for e in entries])

        self.assertIn("LAGO", brands)
        self.assertIn("Pianca", brands)
        self.assertIn("WEB_FLUVU", names)
        self.assertIn("WBCB13C", names)
        self.assertNotIn("._Opera", names)

    def test_scan_keeps_all_supported_formats_for_same_model(self):
        brand = Path(self.test_dir) / "Arredi" / "Letti" / "Twils" / "Opera"
        brand.mkdir(parents=True)
        (brand / "Opera.obj").write_text("dummy")
        (brand / "Opera.3ds").write_text("dummy")
        (brand / "Opera.3dm").write_text("dummy")
        (brand / "Opera.dwg").write_text("dummy")
        (brand / "Opera.max").write_text("ignored")

        entries = [e for e in self.engine.scan_library(self.test_dir) if e.brand == "Twils"]
        formats = sorted([e.format for e in entries])
        self.assertEqual(formats, [".3dm", ".3ds", ".dwg", ".obj"])

    def test_get_formats_filters_by_brand(self):
        brand = Path(self.test_dir) / "Arredi" / "Letti" / "Twils" / "Opera"
        brand.mkdir(parents=True)
        (brand / "Opera.obj").write_text("dummy")
        (brand / "Opera.dwg").write_text("dummy")
        entries = self.engine.scan_library(self.test_dir)
        self.assertEqual(
            self.engine.get_formats(entries, "Arredi", "Letti", "Twils"),
            [".obj", ".dwg"],
        )
        self.assertEqual(
            self.engine.get_formats(entries, "Arredi", "Letti", "Poliform"),
            [".obj"],
        )
        self.assertEqual(
            self.engine.get_models(entries, "Arredi", "Letti", "Twils"),
            ["Opera"],
        )


if __name__ == '__main__':
    unittest.main()
