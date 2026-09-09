from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ModelEntry:
    """Represents a single 3D model in the library."""
    file_path: str
    category: str
    sub_category: str
    brand: str
    model_name: str
    format: str
    thumbnail_path: Optional[str] = None

    def to_binding_dict(self):
        """Returns a dictionary for Eto.Forms GridView data binding."""
        return {
            "ModelName": self.model_name,
            "Brand": self.brand,
            "Format": self.format,
            "FilePath": self.file_path,
            "Category": self.category,
            "SubCategory": self.sub_category,
        }
