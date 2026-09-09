from datetime import datetime


class LibraryIndex(object):
    """Represents the serialized index of the library."""

    def __init__(self, last_scanned=None, entries=None):
        self.last_scanned = last_scanned if last_scanned is not None else datetime.utcnow()
        self.entries = entries if entries is not None else []
