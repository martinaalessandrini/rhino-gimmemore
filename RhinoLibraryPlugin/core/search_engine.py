import re
from typing import List

from .model_entry import ModelEntry


class SearchEngine:
    """Handles query normalization and token-based keyword search."""

    def normalize_query(self, query: str) -> List[str]:
        """Normalizes a query string into lowercase tokens, removing hyphens and underscores."""
        if not query or not query.strip():
            return []
        normalized = query.lower()
        normalized = re.sub(r"[-_]", " ", normalized)
        normalized = re.sub(r"\s+", " ", normalized).strip()
        return [token for token in normalized.split(" ") if token]

    def search(self, query: str, entries: List[ModelEntry]) -> List[ModelEntry]:
        """Filters entries by query. All tokens must be present in at least one field (AND on tokens, OR on fields)."""
        tokens = self.normalize_query(query)
        if not tokens:
            return list(entries)

        results = []
        for entry in entries:
            searchable = f"{entry.category} {entry.sub_category} {entry.brand} {entry.model_name}".lower()
            if all(token in searchable for token in tokens):
                results.append(entry)

        # Sort by relevance: model_name matches first, then brand
        def score(entry: ModelEntry) -> int:
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
