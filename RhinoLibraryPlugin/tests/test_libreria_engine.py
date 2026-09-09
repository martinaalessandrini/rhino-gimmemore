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
        now = datetime.utcnow()
        self.assertFalse(self.engine.is_index_stale(self.test_dir, now))


if __name__ == '__main__':
    unittest.main()
