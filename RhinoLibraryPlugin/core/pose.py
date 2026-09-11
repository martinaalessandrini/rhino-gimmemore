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


def map_obj_point_to_rhino(x, y, z):
    """OBJ Y in alto -> Rhino Z in alto: (x, y, z) -> (x, -z, y)."""
    return (float(x), float(-z), float(y))


def should_align_obj_up_axis(file_format, curve_only):
    """Solo OBJ 3D in GimmeMore; piante 2D e altri formati restano com'erano."""
    if file_format is None:
        return False
    return file_format.lower() == ".obj" and not curve_only
