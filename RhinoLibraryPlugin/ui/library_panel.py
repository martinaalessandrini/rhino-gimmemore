# coding: utf-8
import os
import clr
clr.AddReference("Eto")

import Eto.Forms as forms
import Eto.Drawing as drawing
from datetime import datetime

from core.libreria_engine import LibreriaEngine
from core.search_engine import SearchEngine
from core.library_index import LibraryIndex
from services.thumbnail_manager import ThumbnailManager
from services.import_manager import ImportManager
from settings.plugin_settings import PluginSettings
from core.result_row import ellipsize_label, result_row_fields
from core.column_layout import (
    COLUMN_COUNT,
    apply_weights,
    drag_adjacent_columns,
    equal_column_widths,
    inner_width,
    reset_column_to_standard,
    session_get,
    session_put,
)

FORMAT_LABELS = {
    ".3dm": "3DM",
    ".obj": "OBJ",
    ".3ds": "3DS",
    ".dwg": "DWG",
}
LABEL_TO_FORMAT = {}
for _fmt, _label in FORMAT_LABELS.items():
    LABEL_TO_FORMAT[_label] = _fmt
    LABEL_TO_FORMAT[_label.lower()] = _fmt
    LABEL_TO_FORMAT[_fmt] = _fmt


class LibraryPanel(forms.Panel):
    # IronPython: i keyword extra sul costruttore di un controllo Eto/CLR falliscono.
    _create_pose_mode = False

    def __init__(self):
        pose_mode = LibraryPanel._create_pose_mode
        LibraryPanel._create_pose_mode = False
        super(LibraryPanel, self).__init__()
        self.pose_mode = pose_mode
        self.host_form = None
        if pose_mode:
            gimmemore_file = os.path.join(
                PluginSettings.SETTINGS_DIR, "settings-gimmemore.json"
            )
            self.settings = PluginSettings(
                settings_file=gimmemore_file, default_to_fixture=False
            )
        else:
            self.settings = PluginSettings()
        self.lib_engine = LibreriaEngine()
        self.search_engine = SearchEngine()
        self.thumb_manager = ThumbnailManager(self.settings)
        self.import_manager = ImportManager()
        self.all_entries = []
        self.filtered_entries = []
        self._updating_filters = False
        self._syncing_columns = False
        self._user_resizing = False
        self._drag_col = None
        self._drag_screen_x = 0
        self._drag_widths = None
        self._header_labels = []
        self._filter_dropdowns = []
        self._col_pixel_width = 120
        self._applied_widths = None
        self._column_weights = session_get(self._session_key())

        self.build_layout()
        self.load_library()
        self._sync_columns()

    def build_layout(self):
        self.search_box = forms.TextBox()
        self.search_box.PlaceholderText = "Cerca per categoria, marca, modello..."
        self.search_box.TextChanged += self.on_search_changed

        self.folder_button = forms.Button()
        self.folder_button.Text = "Scegli cartella"
        self.folder_button.Click += self.on_choose_folder

        self.category_dropdown = forms.DropDown()
        self.category_dropdown.Enabled = False
        self.category_dropdown.SelectedIndexChanged += self.on_filter_changed

        self.sub_category_dropdown = forms.DropDown()
        self.sub_category_dropdown.Enabled = False
        self.sub_category_dropdown.SelectedIndexChanged += self.on_filter_changed

        self.brand_dropdown = forms.DropDown()
        self.brand_dropdown.Enabled = False
        self.brand_dropdown.SelectedIndexChanged += self.on_filter_changed

        self.model_dropdown = forms.DropDown()
        self.model_dropdown.Enabled = False
        self.model_dropdown.SelectedIndexChanged += self.on_filter_changed

        self.format_dropdown = forms.DropDown()
        self.format_dropdown.Enabled = False
        self.format_dropdown.SelectedIndexChanged += self.on_filter_changed

        titles = ("Categoria", "Tipo", "Marca", "Modello", "Formato")
        self._filter_dropdowns = [
            self.category_dropdown,
            self.sub_category_dropdown,
            self.brand_dropdown,
            self.model_dropdown,
            self.format_dropdown,
        ]
        self._header_labels = []
        for title in titles:
            lab = forms.Label()
            lab.Text = title
            try:
                lab.Wrap = forms.WrapMode.None
            except Exception:
                pass
            try:
                lab.AutoSize = False
            except Exception:
                pass
            self._header_labels.append(lab)

        columns_table = forms.TableLayout()
        columns_table.Spacing = drawing.Size(0, 4)
        columns_table.Padding = drawing.Padding(0)

        def equal_cell(control):
            cell = forms.TableCell(control)
            cell.ScaleWidth = False
            return cell

        def gutter_cell():
            spacer = forms.Panel()
            spacer.Width = 20
            cell = forms.TableCell(spacer)
            cell.ScaleWidth = False
            return cell

        header_row = forms.TableRow()
        for lab in self._header_labels:
            header_row.Cells.Add(equal_cell(lab))
        header_row.Cells.Add(gutter_cell())

        filter_row = forms.TableRow()
        for drop in self._filter_dropdowns:
            filter_row.Cells.Add(equal_cell(drop))
        filter_row.Cells.Add(gutter_cell())

        columns_table.Rows.Add(header_row)
        columns_table.Rows.Add(filter_row)

        self.results_grid = forms.GridView()
        self.results_grid.ShowHeader = False
        self.results_grid.AllowMultipleSelection = False
        self.results_grid.SelectionChanged += self.on_selection_changed
        self.results_grid.SizeChanged += self._sync_columns
        try:
            self.results_grid.AllowColumnReordering = False
        except Exception:
            pass

        for index, header in enumerate(titles):
            col = forms.GridColumn()
            col.HeaderText = header
            col.DataCell = forms.TextBoxCell(index)
            col.Editable = False
            col.Expand = False
            col.Width = 100
            try:
                col.Resizable = False
            except Exception:
                pass
            self.results_grid.Columns.Add(col)

        for i, lab in enumerate(self._header_labels):
            lab.MouseDoubleClick += self._make_header_reset_handler(i)
            lab.MouseDown += self._make_header_down_handler(i)
            lab.MouseMove += self._make_header_move_handler(i)
            lab.MouseUp += self._on_drag_mouse_up
        self.MouseMove += self._on_drag_mouse_move
        self.MouseUp += self._on_drag_mouse_up
        try:
            self.results_grid.MouseUp += self._on_grid_mouse_up
        except Exception:
            pass

        self.SizeChanged += self._sync_columns

        self.import_button = forms.Button()
        self.import_button.Text = "Importa selezionato"
        self.import_button.Enabled = False
        self.import_button.Click += self.on_import_clicked

        self.refresh_button = forms.Button()
        self.refresh_button.Text = "Aggiorna libreria"

        def on_refresh(s, e):
            self.load_library(force_rescan=True)

        self.refresh_button.Click += on_refresh

        self.status_label = forms.Label()
        self.status_label.Text = "Caricamento..."

        button_layout = forms.DynamicLayout()
        button_layout.BeginHorizontal()
        button_layout.Add(self.folder_button, True)
        button_layout.Add(self.refresh_button, True)
        button_layout.Add(self.import_button, True)
        button_layout.EndHorizontal()

        main_layout = forms.DynamicLayout()
        main_layout.Padding = drawing.Padding(0)
        main_layout.Spacing = drawing.Size(4, 4)
        main_layout.BeginVertical()
        main_layout.Add(self.search_box, True, False)
        main_layout.Add(columns_table, True, False)
        main_layout.Add(self.results_grid, True, True)
        main_layout.Add(button_layout, True, False)
        main_layout.Add(self.status_label, True, False)
        main_layout.EndVertical()

        self.Content = main_layout

    def _session_key(self):
        if getattr(self, "pose_mode", False):
            return "gimmemore"
        return "libreria"

    def _make_header_reset_handler(self, index):
        def handler(sender, e):
            self._reset_column_from_header(index)
        return handler

    def _make_header_down_handler(self, index):
        def handler(sender, e):
            self._on_header_mouse_down(index, sender, e)
        return handler

    def _make_header_move_handler(self, index):
        def handler(sender, e):
            if self._user_resizing:
                self._on_drag_mouse_move(sender, e)
                return
            edge = self._near_column_edge(sender, e)
            try:
                if edge:
                    sender.Cursor = forms.Cursors.VerticalSplit
                else:
                    sender.Cursor = forms.Cursors.Default
            except Exception:
                pass
        return handler

    def _mouse_screen_x(self, sender, e):
        try:
            return int(forms.Mouse.Position.X)
        except Exception:
            pass
        try:
            loc = e.Location
            pt = sender.PointToScreen(drawing.Point(int(loc.X), int(loc.Y)))
            return int(pt.X)
        except Exception:
            pass
        try:
            return int(e.ScreenLocation.X)
        except Exception:
            return None

    def _on_header_mouse_down(self, index, sender, e):
        edge = self._near_column_edge(sender, e)
        if not edge:
            return
        if edge == "left" and index <= 0:
            return
        screen_x = self._mouse_screen_x(sender, e)
        if screen_x is None:
            return
        self._drag_col = index - 1 if edge == "left" else index
        self._user_resizing = True
        self._drag_screen_x = screen_x
        inner = inner_width(self.results_grid.Width)
        self._drag_widths = list(
            self._applied_widths or equal_column_widths(inner)
        )
        try:
            self.Capture = True
        except Exception:
            try:
                forms.Mouse.Capture = self
            except Exception:
                pass

    def _on_drag_mouse_move(self, sender, e):
        if not self._user_resizing or self._drag_col is None or self._drag_widths is None:
            return
        screen_x = self._mouse_screen_x(sender, e)
        if screen_x is None:
            return
        delta = screen_x - self._drag_screen_x
        new = drag_adjacent_columns(self._drag_widths, self._drag_col, delta)
        if new == getattr(self, "_applied_widths", None):
            return
        self._apply_column_pixels(new, update_grid=False)

    def _on_drag_mouse_up(self, sender, e):
        if self._user_resizing and self._drag_col is not None:
            if self._applied_widths:
                self._column_weights = list(self._applied_widths)
                session_put(self._session_key(), self._column_weights)
                self._apply_column_pixels(self._applied_widths, update_grid=True)
            self._fill_grid_rows()
        self._user_resizing = False
        self._drag_col = None
        self._drag_widths = None
        try:
            self.Capture = False
        except Exception:
            try:
                forms.Mouse.Capture = None
            except Exception:
                pass

    def _near_column_edge(self, sender, e):
        try:
            x = int(e.Location.X)
            w = int(sender.Width or 0)
        except Exception:
            return None
        if w <= 0:
            return None
        if x >= w - 10:
            return "right"
        if x <= 10:
            return "left"
        return None

    def _reset_column_from_header(self, index):
        grid = getattr(self, "results_grid", None)
        if grid is None:
            return
        inner = inner_width(grid.Width)
        current = self._column_weights or equal_column_widths(inner)
        widths = reset_column_to_standard(current, index, inner)
        self._column_weights = widths
        session_put(self._session_key(), widths)
        self._apply_column_pixels(widths)
        self._fill_grid_rows()

    def _on_grid_mouse_up(self, sender, e):
        self._capture_user_column_widths()

    def _capture_user_column_widths(self):
        grid = getattr(self, "results_grid", None)
        if grid is None or self._syncing_columns:
            return
        pixels = []
        try:
            for i in range(COLUMN_COUNT):
                pixels.append(int(grid.Columns[i].Width or 0))
        except Exception:
            return
        if len(pixels) < COLUMN_COUNT or min(pixels) <= 0:
            return
        inner = inner_width(grid.Width)
        expected = (
            apply_weights(self._column_weights, inner)
            if self._column_weights
            else equal_column_widths(inner)
        )
        if pixels == expected:
            return
        self._column_weights = pixels
        session_put(self._session_key(), pixels)
        self._apply_column_pixels(pixels)
        self._fill_grid_rows()

    def _apply_column_pixels(self, widths, update_grid=True):
        self._applied_widths = list(widths)
        if widths:
            self._col_pixel_width = min(widths)
        grid = getattr(self, "results_grid", None)
        if grid is None:
            return
        was_syncing = self._syncing_columns
        self._syncing_columns = True
        try:
            for i, w in enumerate(widths):
                if i < len(self._header_labels):
                    try:
                        self._header_labels[i].Width = w
                    except Exception:
                        pass
                if i < len(self._filter_dropdowns):
                    try:
                        self._filter_dropdowns[i].Width = w
                    except Exception:
                        pass
                if update_grid:
                    try:
                        col = grid.Columns[i]
                        col.Expand = False
                        col.Width = w
                    except Exception:
                        pass
        finally:
            self._syncing_columns = was_syncing

    def _fill_grid_rows(self):
        widths = getattr(self, "_applied_widths", None)
        if not widths:
            widths = [getattr(self, "_col_pixel_width", 120)] * COLUMN_COUNT
        rows = []
        for entry in self.filtered_entries:
            fields = result_row_fields(
                entry.category, entry.sub_category, entry.brand, entry.model_name, entry.format
            )
            cells = []
            for i, part in enumerate(fields):
                col_w = widths[i] if i < len(widths) else widths[-1]
                cells.append(ellipsize_label(part, col_w))
            rows.append(tuple(cells))
        self.results_grid.DataStore = rows

    def _sync_columns(self, sender=None, e=None):
        if self._syncing_columns or getattr(self, "_user_resizing", False):
            return
        grid = getattr(self, "results_grid", None)
        if grid is None:
            return
        try:
            n = int(grid.Columns.Count)
        except Exception:
            try:
                n = len(list(grid.Columns))
            except Exception:
                n = 0
        if n < COLUMN_COUNT:
            return
        self._syncing_columns = True
        try:
            total = int(grid.Width or 0)
            if total > 80:
                inner = inner_width(total)
                if self._column_weights:
                    widths = apply_weights(self._column_weights, inner)
                else:
                    widths = equal_column_widths(inner)
                self._apply_column_pixels(widths)
            self._fill_grid_rows()
        finally:
            self._syncing_columns = False

    def on_choose_folder(self, sender, e):
        dialog = forms.SelectFolderDialog()
        dialog.Title = "Scegli la cartella della libreria"
        if self.settings.library_root_path:
            dialog.Directory = self.settings.library_root_path
        result = dialog.ShowDialog(self)
        if result == forms.DialogResult.Ok:
            self.settings.library_root_path = dialog.Directory
            self.settings.save()
            self.load_library()

    def load_library(self, force_rescan=False):
        self.status_label.Text = "Caricamento libreria..."
        root_path = self.settings.library_root_path
        if not root_path:
            if self.pose_mode:
                self.status_label.Text = "Scegli la cartella della libreria per iniziare."
            else:
                self.status_label.Text = "Seleziona la cartella libreria nelle impostazioni del plugin"
            return

        import os
        if not os.path.exists(root_path):
            self.status_label.Text = "Cartella libreria non trovata"
            return

        index = None if force_rescan else self.lib_engine.load_index(root_path)
        if index is None or self.lib_engine.is_index_stale(root_path, index.last_scanned):
            entries = self.lib_engine.scan_library(root_path)
            index = LibraryIndex(last_scanned=datetime.utcnow(), entries=entries)
            self.lib_engine.save_index(root_path, index)

        self.all_entries = index.entries
        self.populate_filter_dropdowns()
        self.apply_filters_and_search()

    def populate_filter_dropdowns(self):
        self._updating_filters = True
        try:
            categories = self.lib_engine.get_categories(self.all_entries)
            self.category_dropdown.Items.Clear()
            self.category_dropdown.Items.Add("Tutte le categorie")
            for cat in categories:
                self.category_dropdown.Items.Add(cat)
            self.category_dropdown.SelectedIndex = 0
            self.category_dropdown.Enabled = True

            self.sub_category_dropdown.Items.Clear()
            self.sub_category_dropdown.Enabled = False
            self.brand_dropdown.Items.Clear()
            self.brand_dropdown.Enabled = False
            self.model_dropdown.Items.Clear()
            self.model_dropdown.Enabled = False
            self._fill_format_dropdown(self.all_entries)
        finally:
            self._updating_filters = False

    def _fill_model_dropdown(self, entries, category, sub_category, brand):
        models = self.lib_engine.get_models(entries, category or "", sub_category or "", brand or "")
        self.model_dropdown.Items.Clear()
        self.model_dropdown.Items.Add("Tutti i modelli")
        for name in models:
            self.model_dropdown.Items.Add(name)
        self.model_dropdown.SelectedIndex = 0
        self.model_dropdown.Enabled = True

    def _fill_format_dropdown(self, entries, category=None, sub_category=None, brand=None, model_name=None):
        formats = self.lib_engine.get_formats(
            entries, category, sub_category, brand, model_name
        )
        self.format_dropdown.Items.Clear()
        self.format_dropdown.Items.Add("Tutti i formati")
        for fmt in formats:
            self.format_dropdown.Items.Add(FORMAT_LABELS.get(fmt, fmt.lstrip(".").upper()))
        self.format_dropdown.SelectedIndex = 0
        self.format_dropdown.Enabled = True

    def _dropdown_text(self, dropdown):
        try:
            idx = int(dropdown.SelectedIndex)
        except Exception:
            return None
        if idx <= 0:
            return None
        value = dropdown.SelectedValue
        if value is None:
            return None
        text = getattr(value, "Text", None)
        if not text:
            text = str(value)
        text = str(text).strip()
        if (not text) or text.startswith("Tutte ") or text.startswith("Tutti "):
            return None
        known = set()
        for entry in self.all_entries:
            known.add(entry.category)
            known.add(entry.sub_category)
            known.add(entry.brand)
            known.add(entry.model_name)
        if text not in known:
            return None
        return text

    def _selected_format(self):
        try:
            idx = int(self.format_dropdown.SelectedIndex)
        except Exception:
            return None
        if idx <= 0:
            return None
        value = self.format_dropdown.SelectedValue
        if value is None:
            return None
        text = getattr(value, "Text", None)
        if not text:
            text = str(value)
        text = str(text).strip()
        if (not text) or text.startswith("Tutti "):
            return None
        mapped = LABEL_TO_FORMAT.get(text)
        if mapped:
            return mapped
        return LABEL_TO_FORMAT.get(text.lower())

    def on_filter_changed(self, sender, e):
        if self._updating_filters:
            return
        selected_category = self._dropdown_text(self.category_dropdown)
        selected_sub = self._dropdown_text(self.sub_category_dropdown)
        selected_brand = self._dropdown_text(self.brand_dropdown)
        selected_model = self._dropdown_text(self.model_dropdown)

        if sender == self.category_dropdown:
            self._updating_filters = True
            try:
                sub_categories = self.lib_engine.get_sub_categories(self.all_entries, selected_category or "")
                self.sub_category_dropdown.Items.Clear()
                self.sub_category_dropdown.Items.Add("Tutti i tipi")
                for sub in sub_categories:
                    self.sub_category_dropdown.Items.Add(sub)
                self.sub_category_dropdown.SelectedIndex = 0
                self.sub_category_dropdown.Enabled = True
                self.brand_dropdown.Items.Clear()
                self.brand_dropdown.Enabled = False
                self.model_dropdown.Items.Clear()
                self.model_dropdown.Enabled = False
                self._fill_format_dropdown(self.all_entries, selected_category)
            finally:
                self._updating_filters = False
        elif sender == self.sub_category_dropdown:
            self._updating_filters = True
            try:
                brands = self.lib_engine.get_brands(self.all_entries, selected_category or "", selected_sub or "")
                self.brand_dropdown.Items.Clear()
                self.brand_dropdown.Items.Add("Tutte le marche")
                for brand in brands:
                    self.brand_dropdown.Items.Add(brand)
                self.brand_dropdown.SelectedIndex = 0
                self.brand_dropdown.Enabled = True
                self.model_dropdown.Items.Clear()
                self.model_dropdown.Enabled = False
                self._fill_format_dropdown(self.all_entries, selected_category, selected_sub)
            finally:
                self._updating_filters = False
        elif sender == self.brand_dropdown:
            self._updating_filters = True
            try:
                self._fill_model_dropdown(
                    self.all_entries, selected_category, selected_sub, selected_brand
                )
                self._fill_format_dropdown(
                    self.all_entries, selected_category, selected_sub, selected_brand
                )
            finally:
                self._updating_filters = False
        elif sender == self.model_dropdown:
            self._updating_filters = True
            try:
                self._fill_format_dropdown(
                    self.all_entries,
                    selected_category,
                    selected_sub,
                    selected_brand,
                    selected_model,
                )
            finally:
                self._updating_filters = False

        self.apply_filters_and_search()

    def on_search_changed(self, sender, e):
        self.apply_filters_and_search()

    def apply_filters_and_search(self):
        pool = list(self.all_entries)
        query = str(self.search_box.Text or "").strip()
        placeholder = str(self.search_box.PlaceholderText or "")
        if query == placeholder:
            query = ""

        if query:
            pool = self.search_engine.search(query, pool)
        else:
            cat = self._dropdown_text(self.category_dropdown)
            if cat:
                pool = [e for e in pool if e.category == cat]
            sub = self._dropdown_text(self.sub_category_dropdown)
            if sub:
                pool = [e for e in pool if e.sub_category == sub]
            brand = self._dropdown_text(self.brand_dropdown)
            if brand:
                pool = [e for e in pool if e.brand == brand]
            model = self._dropdown_text(self.model_dropdown)
            if model:
                pool = [e for e in pool if e.model_name == model]

        fmt = self._selected_format()
        if fmt:
            pool = [e for e in pool if e.format == fmt]

        self.filtered_entries = pool
        self.import_button.Enabled = False
        for drop in self._filter_dropdowns:
            try:
                value = drop.SelectedValue
                tip = getattr(value, "Text", None) or str(value or "")
                drop.ToolTip = str(tip).strip()
            except Exception:
                pass
        self._sync_columns()

        if not self.all_entries:
            self.status_label.Text = "Nessun oggetto in libreria"
        elif query and not self.filtered_entries:
            self.status_label.Text = "Nessun risultato per: {0}".format(query)
        else:
            self.status_label.Text = "{0} oggetti  |  {1}".format(
                len(self.filtered_entries),
                self.settings.library_root_path
            )

    def _selected_row_index(self):
        try:
            return int(self.results_grid.SelectedRow)
        except Exception:
            return -1

    def on_selection_changed(self, sender, e):
        self.import_button.Enabled = self._selected_row_index() >= 0

    def on_import_clicked(self, sender, e):
        idx = self._selected_row_index()
        if idx < 0 or idx >= len(self.filtered_entries):
            return
        entry = self.filtered_entries[idx]
        if self.pose_mode:
            success = self.import_manager.place_model(entry.file_path, self.host_form)
        else:
            success = self.import_manager.import_model(entry.file_path)
        if success:
            print("Importato: {0}".format(entry.model_name))
        else:
            print("Errore importazione: {0}".format(entry.model_name))
