import re

from core.model_entry import ModelEntry


class SearchEngine(object):
    """Handles query normalization and token-based keyword search."""

    def normalize_query(self, query):
        query = "" if query is None else str(query)
        if not query.strip():
            return []
        normalized = query.lower()
        normalized = re.sub(r"[-_]", " ", normalized)
        normalized = re.sub(r"\s+", " ", normalized).strip()
        return [token for token in normalized.split(" ") if token]

    def search(self, query, entries):
        tokens = self.normalize_query(query)
        if not tokens:
            return list(entries)

        results = []
        for entry in entries:
            searchable = (entry.category + " " + entry.sub_category + " " + entry.brand + " " + entry.model_name).lower()
            if all(token in searchable for token in tokens):
                results.append(entry)

        def score(entry):
            model_name_lower = entry.model_name.lower()
            brand_lower = entry.brand.lower()
            s = 0
            for token in tokens:
                if token in model_name_lower:
                    s += 10
                elif token in brand_lower:
                    s += 5
                else:
                    s += 1
            return s

        return sorted(results, key=lambda e: (-score(e), e.model_name))
