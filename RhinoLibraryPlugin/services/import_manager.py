import os

from core.pose import translation_for_pose


class ImportManager(object):
    """Handles importing 3D models into the current Rhino document."""

    SUPPORTED_FORMATS = set([".obj", ".3ds", ".3dm", ".dwg"])

    def can_import(self, file_path):
        if not file_path or not os.path.exists(file_path):
            return False
        return os.path.splitext(file_path)[1].lower() in self.SUPPORTED_FORMATS

    def import_model(self, file_path):
        if not self.can_import(file_path):
            return False
        try:
            import clr
            clr.AddReference("RhinoCommon")
            import Rhino

            doc = Rhino.RhinoDoc.ActiveDoc
            if doc is None:
                return False

            command = '_-Import "{0}" _Enter'.format(file_path)
            return Rhino.RhinoApp.RunScript(command, False)
        except Exception:
            return False

    def _object_ids(self, doc):
        ids = []
        for obj in doc.Objects:
            ids.append(obj.Id)
        return ids

    def _delete_ids(self, doc, ids):
        for obj_id in ids:
            doc.Objects.Delete(obj_id, True)

    def _combined_bbox(self, objects):
        bbox = None
        for obj in objects:
            geo = obj.Geometry
            if geo is None:
                continue
            part = geo.GetBoundingBox(True)
            if part is None or not part.IsValid:
                continue
            if bbox is None:
                bbox = part
            else:
                bbox.Union(part)
        return bbox

    def place_model(self, file_path, host_form=None):
        """Importa e chiede un click XY; il fondo del volume va a Z=0. Esc cancella."""
        if not self.can_import(file_path):
            return False
        try:
            import clr
            clr.AddReference("RhinoCommon")
            import Rhino
            import Rhino.Input
            import Rhino.Input.Custom
            from Rhino.Geometry import Transform

            placed = False
            new_ids = None
            doc = Rhino.RhinoDoc.ActiveDoc
            if doc is None:
                return False

            before = set(self._object_ids(doc))
            command = '_-Import "{0}" _Enter'.format(file_path)
            ok = Rhino.RhinoApp.RunScript(command, False)
            if not ok:
                return False

            new_objs = []
            for obj in doc.Objects:
                if obj.Id not in before:
                    new_objs.append(obj)
            if not new_objs:
                return False

            bbox = self._combined_bbox(new_objs)
            if bbox is None or not bbox.IsValid:
                self._delete_ids(doc, [o.Id for o in new_objs])
                return False

            import Rhino.Geometry as rg
            from System.Drawing import Color

            preview_curves = self._light_curve_preview(new_objs, rg)
            preview_color = Color.FromArgb(255, 0, 140, 220)

            new_ids = [o.Id for o in new_objs]
            for obj_id in new_ids:
                doc.Objects.Hide(obj_id, True)
            doc.Views.Redraw()

            restored_topmost = None
            if host_form is not None:
                try:
                    restored_topmost = host_form.Topmost
                    host_form.Topmost = False
                except Exception:
                    restored_topmost = None

            try:
                gp = Rhino.Input.Custom.GetPoint()
                gp.SetCommandPrompt("Punto di inserimento")

                def on_dynamic_draw(sender, e):
                    try:
                        pt_now = e.CurrentPoint
                        dx, dy, dz = translation_for_pose(
                            bbox.Min.X, bbox.Min.Y, bbox.Min.Z,
                            bbox.Max.X, bbox.Max.Y, bbox.Max.Z,
                            pt_now.X, pt_now.Y,
                        )
                        preview = Transform.Translation(dx, dy, dz)
                        self._draw_pose_preview(
                            e.Display, bbox, preview, preview_color, preview_curves, rg
                        )
                    except Exception:
                        pass

                gp.DynamicDraw += on_dynamic_draw
                get_result = gp.Get()
            finally:
                if host_form is not None and restored_topmost is not None:
                    try:
                        host_form.Topmost = restored_topmost
                    except Exception:
                        pass

            if get_result != Rhino.Input.GetResult.Point:
                self._delete_ids(doc, new_ids)
                doc.Views.Redraw()
                return False

            pt = gp.Point()
            dx, dy, dz = translation_for_pose(
                bbox.Min.X, bbox.Min.Y, bbox.Min.Z,
                bbox.Max.X, bbox.Max.Y, bbox.Max.Z,
                pt.X, pt.Y,
            )
            xform = Transform.Translation(dx, dy, dz)
            for obj_id in new_ids:
                doc.Objects.Transform(obj_id, xform, True)
                doc.Objects.Show(obj_id, True)
            doc.Views.Redraw()
            placed = True
            return True
        except Exception:
            try:
                if (not placed) and new_ids:
                    self._delete_ids(doc, new_ids)
                    doc.Views.Redraw()
            except Exception:
                pass
            return False

    def _light_curve_preview(self, objects, rg):
        """Curve 2D solo se sono poche; altrimenti None e si usa il solo ingombro."""
        curves = []
        for obj in objects:
            geo = obj.Geometry
            if geo is None:
                continue
            if not isinstance(geo, rg.Curve):
                return None
            curves.append(geo)
            if len(curves) > 250:
                return None
        if not curves:
            return None
        return curves

    def _draw_pose_preview(self, display, bbox, xform, color, curves, rg):
        display.PushModelTransform(xform)
        try:
            if curves:
                for curve in curves:
                    display.DrawCurve(curve, color, 2)
            else:
                display.DrawBox(rg.Box(bbox), color)
            cx = (bbox.Min.X + bbox.Max.X) / 2.0
            cy = (bbox.Min.Y + bbox.Max.Y) / 2.0
            cz = bbox.Min.Z
            display.DrawPoint(rg.Point3d(cx, cy, cz), color)
        finally:
            display.PopModelTransform()
