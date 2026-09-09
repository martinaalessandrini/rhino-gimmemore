from dataclasses import dataclass, field
from datetime import datetime
from typing import List
from .model_entry import ModelEntry


@dataclass
class LibraryIndex:
    """Represents the serialized index of the library."""
    last_scanned: datetime = field(default_factory=datetime.utcnow)
    entries: List[ModelEntry] = field(default_factory=list)
