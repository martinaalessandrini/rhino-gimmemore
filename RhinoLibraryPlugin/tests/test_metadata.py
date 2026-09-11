# coding: utf-8
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.metadata import infer_metadata


class InferMetadataTests(unittest.TestCase):
    def test_reads_tipo_and_brand_from_folder_tree(self):
        cat, tipo, brand, model = infer_metadata(
            ["Arredi", "Letti", "Poliform"], "LettoBaba.obj"
        )
        self.assertEqual((cat, tipo, brand, model), ("Arredi", "Letti", "Poliform", "LettoBaba"))

    def test_strips_brand_and_dimension_from_filename(self):
        cat, tipo, brand, model = infer_metadata(
            ["Arredi", "Letti", "Poliform"], "POLIFORM_Letto Baba_3D.obj"
        )
        self.assertEqual(brand, "Poliform")
        self.assertEqual(tipo, "Letti")
        self.assertEqual(model, "Letto Baba")

    def test_strips_matching_brand_prefix_from_stem(self):
        cat, tipo, brand, model = infer_metadata(
            ["Arredi", "Letti", "LAGO"], "LAGO_WEB_FLUVU.obj"
        )
        self.assertEqual(brand, "LAGO")
        self.assertEqual(tipo, "Letti")
        self.assertEqual(model, "WEB_FLUVU")

    def test_numbered_tipo_folder_is_cleaned(self):
        cat, tipo, brand, model = infer_metadata(
            ["Arredi", "01_LETTI", "Pianca"], "WBCB13C.obj"
        )
        self.assertEqual(tipo, "Letti")
        self.assertEqual(brand, "Pianca")
        self.assertEqual(model, "WBCB13C")
