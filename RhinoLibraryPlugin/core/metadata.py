# coding: utf-8
"""Tipo e marchio ricavati da cartelle e nome file."""
import os
import re

_DIM_SUFFIX = re.compile(r"[\s_\-]+(2d[\s_\-]*3d|2d|3d)$", re.I)
_NUMBERED_FOLDER = re.compile(r"^\d{2}[\s_\-]+(.+)$")


def _clean_tipo(name):
    if not name:
        return ""
    match = _NUMBERED_FOLDER.match(name.strip())
    if match:
        name = match.group(1)
    if name.isupper() and len(name) > 1:
        return name.title()
    return name


def _filename_stem(filename):
    return os.path.splitext(filename or "")[0]


def _strip_dimension(stem):
    return _DIM_SUFFIX.sub("", stem).strip(" _-")


def _strip_brand_prefix(stem, brand):
    if not stem or not brand:
        return stem
    pattern = re.compile(
        r"^" + re.escape(brand) + r"[\s_\-]+",
        re.I,
    )
    stripped = pattern.sub("", stem).strip(" _-")
    return stripped or stem


def infer_metadata(folder_parts, filename):
    parts = [p for p in (folder_parts or []) if p]
    category = parts[0] if len(parts) > 0 else ""
    tipo = _clean_tipo(parts[1]) if len(parts) > 1 else ""
    brand = parts[2] if len(parts) > 2 else ""
    stem = _strip_dimension(_filename_stem(filename))
    model = _strip_brand_prefix(stem, brand)
    return (category, tipo, brand, model)
