# coding: utf-8
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.pose import translation_for_pose


class PoseTranslationTests(unittest.TestCase):
    def test_centers_xy_on_click_and_puts_volume_bottom_at_world_zero(self):
        # Volume from (0,0,10) to (10,10,20): center in plan (5,5), bottom at z=10.
        # Click at (100, 200). Only XY come from the click; Z goes to world 0.
        dx, dy, dz = translation_for_pose(
            min_x=0, min_y=0, min_z=10,
            max_x=10, max_y=10, max_z=20,
            click_x=100, click_y=200,
        )
        self.assertEqual((dx, dy, dz), (95, 195, -10))

    def test_click_z_is_ignored(self):
        dx, dy, dz = translation_for_pose(
            min_x=-2, min_y=-2, min_z=-4,
            max_x=2, max_y=2, max_z=6,
            click_x=0, click_y=0,
        )
        self.assertEqual((dx, dy, dz), (0, 0, 4))
