# coding: utf-8
"""Testo visibile nella lista: estensione solo in Formato."""


def format_column_label(file_format):
    if not file_format:
        return ""
    text = str(file_format).strip().lower()
    if not text:
        return ""
    if not text.startswith("."):
        text = "." + text
    return text


def ellipsize_label(text, column_width_px):
    """Accorcia il testo visibile se la colonna e' stretta; i puntini stanno in fondo."""
    value = "" if text is None else str(text)
    try:
        width = int(column_width_px)
    except Exception:
        return value
    if width <= 0:
        return value
    max_chars = int((width - 12) / 7)
    if max_chars < 4:
        max_chars = 4
    if len(value) <= max_chars:
        return value
    keep = max_chars - 3
    if keep < 1:
        keep = 1
    return value[:keep] + "..."


def result_row_fields(category, tipo, brand, model_name, file_format):
    return (
        category,
        tipo,
        brand,
        model_name,
        format_column_label(file_format),
    )
