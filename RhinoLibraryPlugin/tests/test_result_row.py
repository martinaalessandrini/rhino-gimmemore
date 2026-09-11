# coding: utf-8
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.result_row import ellipsize_label, result_row_fields


class ResultRowTests(unittest.TestCase):
    def test_extension_lives_only_in_format_column(self):
        category, tipo, brand, name, fmt = result_row_fields(
            "Arredi", "Letti", "Poliform", "LettoBaba", ".obj"
        )
        self.assertEqual((category, tipo, brand, name, fmt), ("Arredi", "Letti", "Poliform", "LettoBaba", ".obj"))
        self.assertNotIn(".obj", name)
        self.assertNotIn(".obj", brand)
        self.assertNotIn(".obj", tipo)

    def test_long_label_gets_ellipsis_when_column_is_narrow(self):
        short = ellipsize_label("LettoBabaNaturaLunga", 40)
        self.assertTrue(short.endswith("..."))
        self.assertLess(len(short), len("LettoBabaNaturaLunga"))

    def test_short_label_stays_whole_when_column_is_wide(self):
        self.assertEqual(ellipsize_label("LettoBaba", 400), "LettoBaba")
