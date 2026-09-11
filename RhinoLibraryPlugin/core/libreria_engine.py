import json
import os
from datetime import datetime

from core.model_entry import ModelEntry
from core.library_index import LibraryIndex
from core.metadata import infer_metadata


def _open_text(path, mode):
    try:
        return open(path, mode, encoding="utf-8")
    except TypeError:
        import codecs
        enc = "utf-8-sig" if "r" in mode else "utf-8"
        return codecs.open(path, mode, enc)


def _parse_iso(value):
    if not value:
        return datetime.utcnow()
    if value.endswith("Z"):
        value = value[:-1]
    for fmt in ("%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    return datetime.utcnow()


class LibreriaEngine(object):
    """Handles folder scanning, index persistence, and metadata extraction."""

    SUPPORTED_FORMATS = set([".obj", ".3ds", ".3dm", ".dwg"])
    INDEX_FILENAME = "library.json"
    SKIP_DIR_NAMES = set(["__macosx", "__pycache__"])

    def _should_skip_dir(self, name):
        lowered = name.lower()
        if lowered in self.SKIP_DIR_NAMES:
            return True
        if name.startswith("."):
            return True
        return False

    def _collect_models_under_brand(self, brand_dir, category, sub_category, brand, entries):
        for dirpath, dirnames, filenames in os.walk(brand_dir):
            dirnames[:] = [d for d in dirnames if not self._should_skip_dir(d)]
            for name in filenames:
                if name.startswith(".") or name.startswith("._"):
                    continue
                ext = os.path.splitext(name)[1].lower()
                if ext not in self.SUPPORTED_FORMATS:
                    continue
                file_path = os.path.join(dirpath, name)
                if not os.path.isfile(file_path):
                    continue
                model_name = os.path.splitext(name)[0]
                thumb_path = os.path.join(dirpath, model_name + ".thumb.png")
                category_out, tipo, brand_out, model_out = infer_metadata(
                    [category, sub_category, brand], name
                )
                entries.append(ModelEntry(
                    file_path=file_path,
                    category=category_out or category,
                    sub_category=tipo or sub_category,
                    brand=brand_out or brand,
                    model_name=model_out or model_name,
                    format=ext,
                    thumbnail_path=thumb_path if os.path.exists(thumb_path) else None
                ))

    def scan_library(self, root_path):
        entries = []
        if not os.path.isdir(root_path):
            return entries

        for category in os.listdir(root_path):
            category_dir = os.path.join(root_path, category)
            if not os.path.isdir(category_dir):
                continue
            if self._should_skip_dir(category):
                continue
            for sub_category in os.listdir(category_dir):
                sub_dir = os.path.join(category_dir, sub_category)
                if not os.path.isdir(sub_dir):
                    continue
                if self._should_skip_dir(sub_category):
                    continue
                for brand in os.listdir(sub_dir):
                    brand_dir = os.path.join(sub_dir, brand)
                    if not os.path.isdir(brand_dir):
                        continue
                    if self._should_skip_dir(brand):
                        continue
                    self._collect_models_under_brand(
                        brand_dir, category, sub_category, brand, entries
                    )
        return entries

    def save_index(self, root_path, index):
        index_path = os.path.join(root_path, self.INDEX_FILENAME)
        data = {
            "lastScanned": index.last_scanned.isoformat() + "Z",
            "entries": [
                {
                    "filePath": e.file_path,
                    "category": e.category,
                    "subCategory": e.sub_category,
                    "brand": e.brand,
                    "modelName": e.model_name,
                    "format": e.format,
                    "thumbnailPath": e.thumbnail_path
                }
                for e in index.entries
            ]
        }
        f = _open_text(index_path, "w")
        try:
            json.dump(data, f, indent=2, ensure_ascii=False)
        finally:
            f.close()

    def load_index(self, root_path):
        index_path = os.path.join(root_path, self.INDEX_FILENAME)
        if not os.path.exists(index_path):
            return None
        try:
            f = _open_text(index_path, "r")
            try:
                data = json.load(f)
            finally:
                f.close()
            entries = []
            for e in data.get("entries", []):
                file_path = e["filePath"]
                try:
                    rel_dir = os.path.dirname(os.path.relpath(file_path, root_path))
                except Exception:
                    rel_dir = ""
                if rel_dir in (".", ""):
                    parts = [e.get("category"), e.get("subCategory"), e.get("brand")]
                else:
                    parts = rel_dir.split(os.sep)[:3]
                category, tipo, brand, model = infer_metadata(
                    parts,
                    os.path.basename(file_path),
                )
                entries.append(ModelEntry(
                    file_path=file_path,
                    category=category or e["category"],
                    sub_category=tipo or e["subCategory"],
                    brand=brand or e["brand"],
                    model_name=model or e["modelName"],
                    format=e["format"],
                    thumbnail_path=e.get("thumbnailPath")
                ))
            last_scanned = _parse_iso(data.get("lastScanned", ""))
            return LibraryIndex(last_scanned=last_scanned, entries=entries)
        except Exception:
            return None

    def is_index_stale(self, root_path, last_scanned):
        if not os.path.isdir(root_path):
            return True
        max_write_time = datetime.min
        for dirpath, dirnames, filenames in os.walk(root_path):
            for name in filenames:
                path = os.path.join(dirpath, name)
                try:
                    mtime = datetime.utcfromtimestamp(os.path.getmtime(path))
                except Exception:
                    continue
                if mtime > max_write_time:
                    max_write_time = mtime
        return max_write_time > last_scanned

    def get_categories(self, entries):
        return sorted(set([e.category for e in entries]))

    def get_sub_categories(self, entries, category):
        return sorted(set([e.sub_category for e in entries if e.category == category]))

    def get_brands(self, entries, category, sub_category):
        return sorted(set([
            e.brand for e in entries
            if e.category == category and e.sub_category == sub_category
        ]))

    def get_models(self, entries, category, sub_category, brand):
        return sorted(set([
            e.model_name for e in entries
            if e.category == category and e.sub_category == sub_category and e.brand == brand
        ]))

    def get_formats(self, entries, category=None, sub_category=None, brand=None, model_name=None):
        found = set()
        for entry in entries:
            if category and entry.category != category:
                continue
            if sub_category and entry.sub_category != sub_category:
                continue
            if brand and entry.brand != brand:
                continue
            if model_name and entry.model_name != model_name:
                continue
            found.add(entry.format)
        preferred = [".3dm", ".obj", ".3ds", ".dwg"]
        result = [fmt for fmt in preferred if fmt in found]
        extras = sorted([fmt for fmt in found if fmt not in preferred])
        return result + extras
