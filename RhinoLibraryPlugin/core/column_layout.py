# coding: utf-8
"""Larghezze colonne lista: uguali di default, regolabili, memoria solo in sessione Rhino."""

COLUMN_COUNT = 5
GUTTER_PX = 20
MIN_COLUMN_PX = 48

_session = {}


def session_reset_for_tests():
    _session.clear()


def session_get(command_key):
    stored = _session.get(command_key)
    if stored is None:
        return None
    return list(stored)


def session_put(command_key, weights):
    _session[command_key] = list(weights)


def inner_width(total_grid_width):
    try:
        total = int(total_grid_width or 0)
    except Exception:
        total = 0
    inner = total - GUTTER_PX
    floor = COLUMN_COUNT * MIN_COLUMN_PX
    if inner < floor:
        return floor
    return inner


def equal_column_widths(inner, count=None):
    if count is None:
        count = COLUMN_COUNT
    try:
        usable = int(inner)
    except Exception:
        usable = 0
    floor = count * MIN_COLUMN_PX
    if usable < floor:
        usable = floor
    base = usable // count
    leftover = usable - (base * count)
    widths = [base] * count
    widths[-1] += leftover
    return widths


def apply_weights(weights, inner, count=None):
    if count is None:
        count = COLUMN_COUNT
    try:
        usable = int(inner)
    except Exception:
        usable = 0
    floor = count * MIN_COLUMN_PX
    if usable < floor:
        usable = floor
    values = []
    if weights:
        for item in list(weights)[:count]:
            try:
                n = int(item)
            except Exception:
                n = 0
            if n < 1:
                n = 1
            values.append(n)
    while len(values) < count:
        values.append(1)
    total = 0
    for n in values:
        total += n
    if total <= 0:
        return equal_column_widths(usable, count)
    widths = []
    allocated = 0
    for i in range(count):
        if i == count - 1:
            w = usable - allocated
        else:
            w = int((values[i] * usable) / total)
        if w < MIN_COLUMN_PX:
            w = MIN_COLUMN_PX
        widths.append(w)
        allocated += w
    extra = sum(widths) - usable
    if extra != 0:
        widths[-1] -= extra
        if widths[-1] < MIN_COLUMN_PX:
            widths[-1] = MIN_COLUMN_PX
    return widths


def reset_column_to_standard(weights, index, inner):
    equal = equal_column_widths(inner)
    try:
        idx = int(index)
    except Exception:
        idx = 0
    if idx < 0 or idx >= COLUMN_COUNT:
        return equal
    target = equal[idx]
    source = list(weights) if weights else list(equal)
    while len(source) < COLUMN_COUNT:
        source.append(equal[0])
    others = []
    for i in range(COLUMN_COUNT):
        if i == idx:
            continue
        try:
            n = int(source[i])
        except Exception:
            n = 1
        if n < 1:
            n = 1
        others.append(n)
    remaining_space = sum(equal) - target
    scaled_others = apply_weights(others, remaining_space, count=COLUMN_COUNT - 1)
    result = []
    other_i = 0
    for i in range(COLUMN_COUNT):
        if i == idx:
            result.append(target)
        else:
            result.append(scaled_others[other_i])
            other_i += 1
    delta = sum(result) - sum(equal)
    if delta != 0:
        for i in range(COLUMN_COUNT - 1, -1, -1):
            if i == idx:
                continue
            result[i] -= delta
            if result[i] < MIN_COLUMN_PX:
                result[i] = MIN_COLUMN_PX
            break
    return result


def drag_adjacent_columns(widths, index, delta_px):
    """Sposta il divisore tra index e index+1 usando un delta in pixel schermo."""
    new = list(widths)
    try:
        i = int(index)
        delta = int(delta_px)
    except Exception:
        return new
    if i < 0 or i >= len(new):
        return new
    if i + 1 < len(new):
        new[i] = widths[i] + delta
        new[i + 1] = widths[i + 1] - delta
        if new[i] < MIN_COLUMN_PX:
            shift = MIN_COLUMN_PX - new[i]
            new[i] = MIN_COLUMN_PX
            new[i + 1] -= shift
        if new[i + 1] < MIN_COLUMN_PX:
            shift = MIN_COLUMN_PX - new[i + 1]
            new[i + 1] = MIN_COLUMN_PX
            new[i] -= shift
    else:
        new[i] = widths[i] + delta
        if new[i] < MIN_COLUMN_PX:
            new[i] = MIN_COLUMN_PX
    return new
