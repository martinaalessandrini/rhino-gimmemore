import json
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from .model_entry import ModelEntry
from .library_index import LibraryIndex


class LibreriaEngine:
    """Handles folder scanning, index persistence, and metadata extraction."""

    SUPPORTED_FORMATS = {".obj", ".3ds", ".3dm"}
    INDEX_FILENAME = "library.json"

    def scan_library(self, root_path: str) -> List[ModelEntry]:
        """Scans the library folder structure and returns a list of ModelEntry."""
        entries = []
        root = Path(root_path)
        if not root.exists():
            return entries

        for category_dir in [d for d in root.iterdir() if d.is_dir()]:
            category = category_dir.name
            for sub_category_dir in [d for d in category_dir.iterdir() if d.is_dir()]:
                sub_category = sub_category_dir.name
                for brand_dir in [d for d in sub_category_dir.iterdir() if d.is_dir()]:
                    brand = brand_dir.name
                    for file_path in brand_dir.iterdir():
                        if not file_path.is_file():
                            continue
                        ext = file_path.suffix.lower()
                        if ext not in self.SUPPORTED_FORMATS:
                            continue

                        model_name = file_path.stem
                        thumb_path = brand_dir / f"{model_name}.thumb.png"

                        entries.append(ModelEntry(
                            file_path=str(file_path),
                            category=category,
                            sub_category=sub_category,
                            brand=brand,
                            model_name=model_name,
                            format=ext,
                            thumbnail_path=str(thumb_path) if thumb_path.exists() else None
                        ))
        return entries

    def save_index(self, root_path: str, index: LibraryIndex) -> None:
        """Saves the index to library.json in the root folder."""
        index_path = Path(root_path) / self.INDEX_FILENAME
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
        with open(index_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def load_index(self, root_path: str) -> Optional[LibraryIndex]:
        """Loads the index from library.json. Returns None if not found or corrupted."""
        index_path = Path(root_path) / self.INDEX_FILENAME
        if not index_path.exists():
            return None
        try:
            with open(index_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            entries = [
                ModelEntry(
                    file_path=e["filePath"],
                    category=e["category"],
                    sub_category=e["subCategory"],
                    brand=e["brand"],
                    model_name=e["modelName"],
                    format=e["format"],
                    thumbnail_path=e.get("thumbnailPath")
                )
                for e in data.get("entries", [])
            ]
            last_scanned_str = data.get("lastScanned", "")
            if last_scanned_str.endswith("Z"):
                last_scanned_str = last_scanned_str[:-1]
            last_scanned = datetime.fromisoformat(last_scanned_str) if last_scanned_str else datetime.utcnow()
            return LibraryIndex(last_scanned=last_scanned, entries=entries)
        except Exception:
            return None

    def is_index_stale(self, root_path: str, last_scanned: datetime) -> bool:
        """Returns True if any file in the library was modified after last_scanned."""
        root = Path(root_path)
        if not root.exists():
            return True

        max_write_time = datetime.min
        for file in root.rglob("*"):
            if file.is_file():
                mtime = datetime.utcfromtimestamp(file.stat().st_mtime)
                if mtime > max_write_time:
                    max_write_time = mtime
        return max_write_time > last_scanned

    def get_categories(self, entries: List[ModelEntry]) -> List[str]:
        """Returns sorted list of unique categories."""
        return sorted({e.category for e in entries})

    def get_sub_categories(self, entries: List[ModelEntry], category: str) -> List[str]:
        """Returns sorted list of unique sub-categories for a given category."""
        return sorted({e.sub_category for e in entries if e.category == category})

    def get_brands(self, entries: List[ModelEntry], category: str, sub_category: str) -> List[str]:
        """Returns sorted list of unique brands for a given category and sub-category."""
        return sorted({e.brand for e in entries if e.category == category and e.sub_category == sub_category})
