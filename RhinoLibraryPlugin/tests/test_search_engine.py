import unittest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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
