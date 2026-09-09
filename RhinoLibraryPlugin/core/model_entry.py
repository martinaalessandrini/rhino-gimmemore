class ModelEntry(object):
    """Represents a single 3D model in the library."""

    def __init__(self, file_path, category, sub_category, brand, model_name, format, thumbnail_path=None):
        self.file_path = file_path
        self.category = category
        self.sub_category = sub_category
        self.brand = brand
        self.model_name = model_name
        self.format = format
        self.thumbnail_path = thumbnail_path

    def to_binding_dict(self):
        return {
            "ModelName": self.model_name,
            "Brand": self.brand,
            "Format": self.format,
            "FilePath": self.file_path,
            "Category": self.category,
            "SubCategory": self.sub_category,
        }
