"""Puro calcolo della posa GimmeMore: click XY + fondo volume a Z=0."""


def translation_for_pose(min_x, min_y, min_z, max_x, max_y, max_z, click_x, click_y):
    center_x = (min_x + max_x) / 2.0
    center_y = (min_y + max_y) / 2.0
    dx = click_x - center_x
    dy = click_y - center_y
    dz = 0.0 - min_z
    return (dx, dy, dz)


def scale_origin_for_pose(click_x, click_y):
    """Origine Scala: punto di inserimento (click XY, Z=0 del disegno)."""
    return (float(click_x), float(click_y), 0.0)
