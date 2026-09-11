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


def result_row_fields(model_name, brand, file_format):
    return (model_name, brand, format_column_label(file_format))
