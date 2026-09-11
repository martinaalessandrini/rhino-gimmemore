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

        self.build_layout()
        self.load_library()

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

        self.format_dropdown = forms.DropDown()
        self.format_dropdown.Enabled = False
        self.format_dropdown.SelectedIndexChanged += self.on_filter_changed

        filter_layout = forms.DynamicLayout()
        filter_layout.BeginHorizontal()
        filter_layout.Add(self.category_dropdown, True)
        filter_layout.Add(self.sub_category_dropdown, True)
        filter_layout.Add(self.brand_dropdown, True)
        filter_layout.Add(self.format_dropdown, True)
        filter_layout.EndHorizontal()

        self.results_list = forms.ListBox()
        self.results_list.SelectedIndexChanged += self.on_selection_changed

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
        main_layout.Add(filter_layout, True, False)
        main_layout.Add(self.results_list, True, True)
        main_layout.Add(button_layout, True, False)
        main_layout.Add(self.status_label, True, False)
        main_layout.EndVertical()

        self.Content = main_layout

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
            self._fill_format_dropdown(self.all_entries)
        finally:
            self._updating_filters = False

    def _fill_format_dropdown(self, entries, category=None, sub_category=None, brand=None):
        formats = self.lib_engine.get_formats(entries, category, sub_category, brand)
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
        if (not text) or text.startswith("Tutte "):
            return None
        known = set()
        for entry in self.all_entries:
            known.add(entry.category)
            known.add(entry.sub_category)
            known.add(entry.brand)
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

        if sender == self.category_dropdown:
            self._updating_filters = True
            try:
                sub_categories = self.lib_engine.get_sub_categories(self.all_entries, selected_category or "")
                self.sub_category_dropdown.Items.Clear()
                self.sub_category_dropdown.Items.Add("Tutte le sottocategorie")
                for sub in sub_categories:
                    self.sub_category_dropdown.Items.Add(sub)
                self.sub_category_dropdown.SelectedIndex = 0
                self.sub_category_dropdown.Enabled = True
                self.brand_dropdown.Items.Clear()
                self.brand_dropdown.Enabled = False
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
                self._fill_format_dropdown(self.all_entries, selected_category, selected_sub)
            finally:
                self._updating_filters = False
        elif sender == self.brand_dropdown:
            self._updating_filters = True
            try:
                self._fill_format_dropdown(
                    self.all_entries, selected_category, selected_sub, selected_brand
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

        fmt = self._selected_format()
        if fmt:
            pool = [e for e in pool if e.format == fmt]

        self.filtered_entries = pool
        self.results_list.Items.Clear()
        for entry in self.filtered_entries:
            self.results_list.Items.Add(
                "{0}  -  {1}  ({2})".format(entry.model_name, entry.brand, entry.format)
            )

        if not self.all_entries:
            self.status_label.Text = "Nessun oggetto in libreria"
        elif query and not self.filtered_entries:
            self.status_label.Text = "Nessun risultato per: {0}".format(query)
        else:
            self.status_label.Text = "{0} oggetti  |  {1}".format(
                len(self.filtered_entries),
                self.settings.library_root_path
            )

    def on_selection_changed(self, sender, e):
        self.import_button.Enabled = self.results_list.SelectedIndex >= 0

    def on_import_clicked(self, sender, e):
        idx = self.results_list.SelectedIndex
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
