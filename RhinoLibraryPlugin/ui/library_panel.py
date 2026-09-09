"""Eto.Forms Dockable Panel for the Rhino Library Plugin."""

import clr
clr.AddReference("Eto")

import Eto.Forms as forms
import Eto.Drawing as drawing
import threading

from core.libreria_engine import LibreriaEngine
from core.search_engine import SearchEngine
from core.library_index import LibraryIndex
from core.model_entry import ModelEntry
from services.thumbnail_manager import ThumbnailManager
from services.import_manager import ImportManager
from settings.plugin_settings import PluginSettings
from datetime import datetime


class LibraryPanel(forms.Panel):
    """Dockable panel with search bar, cascading filters, results grid, and import button."""

    def __init__(self):
        super().__init__()
        self.settings = PluginSettings()
        self.lib_engine = LibreriaEngine()
        self.search_engine = SearchEngine()
        self.thumb_manager = ThumbnailManager(self.settings)
        self.import_manager = ImportManager()
        self.all_entries = []
        self.filtered_entries = []

        self.build_layout()
        threading.Thread(target=self.load_library_async, daemon=True).start()

    def build_layout(self):
        # Search bar
        self.search_box = forms.TextBox()
        self.search_box.PlaceholderText = "Cerca per categoria, marca, modello..."
        self.search_box.TextChanged += self.on_search_changed

        # Filter dropdowns
        self.category_dropdown = forms.DropDown()
        self.category_dropdown.Enabled = False
        self.category_dropdown.SelectedIndexChanged += self.on_filter_changed

        self.sub_category_dropdown = forms.DropDown()
        self.sub_category_dropdown.Enabled = False
        self.sub_category_dropdown.SelectedIndexChanged += self.on_filter_changed

        self.brand_dropdown = forms.DropDown()
        self.brand_dropdown.Enabled = False
        self.brand_dropdown.SelectedIndexChanged += self.on_filter_changed

        filter_layout = forms.DynamicLayout()
        filter_layout.BeginHorizontal()
        filter_layout.Add(self.category_dropdown, True)
        filter_layout.Add(self.sub_category_dropdown, True)
        filter_layout.Add(self.brand_dropdown, True)
        filter_layout.EndHorizontal()

        # Results grid
        self.results_grid = forms.GridView()
        self.setup_results_grid()

        # Import button
        self.import_button = forms.Button()
        self.import_button.Text = "Importa selezionato"
        self.import_button.Enabled = False
        self.import_button.Click += self.on_import_clicked

        # Bottom bar
        self.refresh_button = forms.Button()
        self.refresh_button.Text = "Aggiorna libreria"
        self.refresh_button.Click += lambda s, e: threading.Thread(target=self.load_library_async, daemon=True).start()

        self.status_label = forms.Label()
        self.status_label.Text = "Caricamento..."

        bottom_layout = forms.DynamicLayout()
        bottom_layout.BeginHorizontal()
        bottom_layout.Add(self.refresh_button)
        bottom_layout.Add(self.import_button)
        bottom_layout.Add(self.status_label, True)
        bottom_layout.EndHorizontal()

        # Main layout
        main_layout = forms.DynamicLayout()
        main_layout.BeginVertical()
        main_layout.Add(self.search_box)
        main_layout.Add(filter_layout)
        main_layout.Add(self.results_grid, True)
        main_layout.Add(bottom_layout)
        main_layout.EndVertical()

        self.Content = main_layout

    def setup_results_grid(self):
        self.results_grid.Columns.Add(forms.GridColumn(
            HeaderText="Anteprima",
            DataCell=forms.TextBoxCell("ModelName")  # Simplified: show name as proxy
        ))
        self.results_grid.Columns.Add(forms.GridColumn(
            HeaderText="Nome",
            DataCell=forms.TextBoxCell("ModelName")
        ))
        self.results_grid.Columns.Add(forms.GridColumn(
            HeaderText="Marca",
            DataCell=forms.TextBoxCell("Brand")
        ))
        self.results_grid.Columns.Add(forms.GridColumn(
            HeaderText="Formato",
            DataCell=forms.TextBoxCell("Format")
        ))

        self.results_grid.SelectionChanged += self.on_selection_changed

    def load_library_async(self):
        """Loads the library index or rescans if stale."""
        self.status_label.Text = "Caricamento libreria..."
        root_path = self.settings.library_root_path
        if not root_path:
            self.status_label.Text = "Seleziona la cartella libreria nelle impostazioni del plugin"
            return

        import os
        if not os.path.exists(root_path):
            self.status_label.Text = "Cartella libreria non trovata"
            return

        index = self.lib_engine.load_index(root_path)
        if index is None or self.lib_engine.is_index_stale(root_path, index.last_scanned):
            entries = self.lib_engine.scan_library(root_path)
            index = LibraryIndex(last_scanned=datetime.utcnow(), entries=entries)
            self.lib_engine.save_index(root_path, index)

        self.all_entries = index.entries
        self.populate_filter_dropdowns()
        self.apply_filters_and_search()
        self.status_label.Text = f"{len(self.all_entries)} oggetti trovati"

    def populate_filter_dropdowns(self):
        categories = self.lib_engine.get_categories(self.all_entries)
        self.category_dropdown.Items.Clear()
        self.category_dropdown.Items.Add("Tutte le categorie")
        for cat in categories:
            self.category_dropdown.Items.Add(cat)
        self.category_dropdown.SelectedIndex = 0
        self.category_dropdown.Enabled = True

    def on_filter_changed(self, sender, e):
        selected_category = self.category_dropdown.SelectedValue if self.category_dropdown.SelectedIndex > 0 else None
        selected_sub = self.sub_category_dropdown.SelectedValue if self.sub_category_dropdown.SelectedIndex > 0 else None

        if sender == self.category_dropdown:
            sub_categories = self.lib_engine.get_sub_categories(self.all_entries, selected_category or "")
            self.sub_category_dropdown.Items.Clear()
            self.sub_category_dropdown.Items.Add("Tutte le sottocategorie")
            for sub in sub_categories:
                self.sub_category_dropdown.Items.Add(sub)
            self.sub_category_dropdown.SelectedIndex = 0
            self.sub_category_dropdown.Enabled = True

            self.brand_dropdown.Items.Clear()
            self.brand_dropdown.Enabled = False
        elif sender == self.sub_category_dropdown:
            brands = self.lib_engine.get_brands(self.all_entries, selected_category or "", selected_sub or "")
            self.brand_dropdown.Items.Clear()
            self.brand_dropdown.Items.Add("Tutte le marche")
            for brand in brands:
                self.brand_dropdown.Items.Add(brand)
            self.brand_dropdown.SelectedIndex = 0
            self.brand_dropdown.Enabled = True

        self.apply_filters_and_search()

    def on_search_changed(self, sender, e):
        self.apply_filters_and_search()

    def apply_filters_and_search(self):
        pool = list(self.all_entries)

        if self.category_dropdown.SelectedIndex > 0:
            cat = self.category_dropdown.SelectedValue
            pool = [e for e in pool if e.category == cat]
        if self.sub_category_dropdown.SelectedIndex > 0:
            sub = self.sub_category_dropdown.SelectedValue
            pool = [e for e in pool if e.sub_category == sub]
        if self.brand_dropdown.SelectedIndex > 0:
            brand = self.brand_dropdown.SelectedValue
            pool = [e for e in pool if e.brand == brand]

        query = self.search_box.Text
        if query and query.strip():
            pool = self.search_engine.search(query, pool)

        self.filtered_entries = pool
        self.results_grid.DataStore = [e.to_binding_dict() for e in self.filtered_entries]

        if not self.filtered_entries:
            self.status_label.Text = "Nessun risultato trovato"
        else:
            self.status_label.Text = f"{len(self.filtered_entries)} risultati"

    def on_selection_changed(self, sender, e):
        self.import_button.Enabled = self.results_grid.SelectedItem is not None

    def on_import_clicked(self, sender, e):
        selected = self.results_grid.SelectedItem
        if selected is None:
            return

        # Retrieve the actual ModelEntry from filtered_entries by matching file_path
        file_path = selected.get("FilePath")
        entry = next((en for en in self.filtered_entries if en.file_path == file_path), None)
        if entry is None:
            return

        success = self.import_manager.import_model(entry.file_path)
        if success:
            print(f"Importato: {entry.model_name}")
        else:
            print(f"Errore importazione: {entry.model_name}")
