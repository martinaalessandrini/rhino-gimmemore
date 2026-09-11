# coding: utf-8
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.column_layout import (
    COLUMN_COUNT,
    apply_weights,
    drag_adjacent_columns,
    equal_column_widths,
    inner_width,
    reset_column_to_standard,
    session_get,
    session_put,
    session_reset_for_tests,
)


class EqualColumnTests(unittest.TestCase):
    def test_five_equal_columns_fill_the_inner_width(self):
        widths = equal_column_widths(500)
        self.assertEqual(len(widths), COLUMN_COUNT)
        self.assertEqual(widths, [100, 100, 100, 100, 100])
        self.assertEqual(sum(widths), 500)

    def test_leftover_pixels_go_to_the_last_column(self):
        widths = equal_column_widths(502)
        self.assertEqual(widths, [100, 100, 100, 100, 102])
        self.assertEqual(sum(widths), 502)


class InnerWidthTests(unittest.TestCase):
    def test_scrollbar_gutter_is_taken_from_the_grid(self):
        self.assertEqual(inner_width(520), 500)


class WeightTests(unittest.TestCase):
    def test_stored_weights_scale_to_the_current_window(self):
        widths = apply_weights([2, 1, 1, 1, 1], 600)
        self.assertEqual(sum(widths), 600)
        self.assertEqual(widths[0], widths[1] * 2)

    def test_double_click_restores_that_column_to_equal_share(self):
        current = [240, 90, 90, 90, 90]
        reset = reset_column_to_standard(current, 0, 600)
        equal = equal_column_widths(600)
        self.assertEqual(reset[0], equal[0])
        self.assertEqual(sum(reset), 600)
        self.assertEqual(reset[1], reset[2])
        self.assertEqual(reset[2], reset[3])
        self.assertEqual(reset[3], reset[4])


class DragTests(unittest.TestCase):
    def test_dragging_a_divider_moves_only_the_two_neighbours(self):
        start = [100, 100, 100, 100, 100]
        moved = drag_adjacent_columns(start, 0, 40)
        self.assertEqual(moved, [140, 60, 100, 100, 100])
        self.assertEqual(sum(moved), 500)

    def test_larger_screen_delta_from_the_same_start_only_grows_that_column(self):
        start = [100, 100, 100, 100, 100]
        a = drag_adjacent_columns(start, 0, 10)
        b = drag_adjacent_columns(start, 0, 30)
        self.assertLess(a[0], b[0])
        self.assertGreater(a[1], b[1])



class SessionMemoryTests(unittest.TestCase):
    def setUp(self):
        session_reset_for_tests()

    def test_fresh_rhino_session_has_no_remembered_widths(self):
        self.assertIsNone(session_get("gimmemore"))
        self.assertIsNone(session_get("libreria"))

    def test_each_command_remembers_its_own_widths_until_rhino_exits(self):
        session_put("gimmemore", [200, 100, 100, 100, 100])
        self.assertEqual(session_get("gimmemore"), [200, 100, 100, 100, 100])
        self.assertIsNone(session_get("libreria"))
