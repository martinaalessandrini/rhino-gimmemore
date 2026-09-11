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
        self._header_labels = []
        self._filter_dropdowns = []
        self._col_pixel_width = 120

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
            self._header_labels.append(lab)

        columns_table = forms.TableLayout()
        columns_table.Spacing = drawing.Size(0, 4)
        columns_table.Padding = drawing.Padding(0)

        def equal_cell(control):
            cell = forms.TableCell(control)
            cell.ScaleWidth = True
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
        self.results_grid.ShowHeader = True
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

    def _fill_grid_rows(self):
        width = getattr(self, "_col_pixel_width", 120)
        rows = []
        for entry in self.filtered_entries:
            fields = result_row_fields(
                entry.category, entry.sub_category, entry.brand, entry.model_name, entry.format
            )
            rows.append(tuple(ellipsize_label(part, width) for part in fields))
        self.results_grid.DataStore = rows

    def _sync_columns(self, sender=None, e=None):
        if self._syncing_columns:
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
        if n < 5:
            return
        self._syncing_columns = True
        try:
            total = int(grid.Width or 0)
            count = 5
            if total > 80:
                gutter = 20
                inner = total - gutter
                if inner < count * 48:
                    inner = count * 48
                col_w = int(inner / count)
                leftover = inner - (col_w * count)
                for i in range(count):
                    w = col_w
                    if i == count - 1:
                        w += leftover
                    col = grid.Columns[i]
                    col.Expand = False
                    col.Width = w
                self._col_pixel_width = col_w
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
