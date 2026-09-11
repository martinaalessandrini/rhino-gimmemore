# coding: utf-8
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.result_row import result_row_fields


class ResultRowTests(unittest.TestCase):
    def test_extension_lives_only_in_format_column(self):
        name, brand, fmt = result_row_fields("LettoBaba", "Poliform", ".obj")
        self.assertEqual(name, "LettoBaba")
        self.assertEqual(brand, "Poliform")
        self.assertEqual(fmt, ".obj")
        self.assertNotIn(".obj", name)
        self.assertNotIn(".obj", brand)
