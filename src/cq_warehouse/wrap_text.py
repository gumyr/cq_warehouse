from math import pi, sin, cos, sqrt
import cadquery as cq
from cadquery import Vector, Shape
from typing import Optional, Literal
from cadquery.occ_impl.shapes import edgesToWires
import timeit

from OCP.Font import (
    Font_FontMgr,
    Font_FA_Regular,
    Font_FA_Italic,
    Font_FA_Bold,
    Font_SystemFont,
)
from OCP.TCollection import TCollection_AsciiString
from OCP.StdPrs import StdPrs_BRepFont, StdPrs_BRepTextBuilder as Font_BRepTextBuilder
from OCP.NCollection import NCollection_Utf8String
from OCP.ShapeAnalysis import ShapeAnalysis_FreeBounds
from OCP.TopTools import TopTools_HSequenceOfShape
from OCP.BRepOffset import BRepOffset_MakeOffset, BRepOffset_Skin
from OCP.GeomAbs import GeomAbs_Intersection


def sortWires(wires: list[cq.Wire]) -> tuple[list[cq.Wire], list[cq.Wire]]:
    """Sort a list of wires into lists of outside and inside wires"""
    faces_from_wires = [cq.Face.makeFromWires(w, []) for w in wires]
    area_of_wires = [f.Area() for f in faces_from_wires]
    inside_wire_indices = []
    for o, f_outer in enumerate(faces_from_wires):
        if o in inside_wire_indices:
            continue
        for i, f_inner in enumerate(faces_from_wires):
            if f_outer is f_inner:
                continue
            if f_outer.cut(f_inner).Area() < area_of_wires[o]:
                inside_wire_indices.append(i)
    outside_wire_indices = [
        o for o in range(len(wires)) if not o in inside_wire_indices
    ]
    inner_wires = [wires[i] for i in inside_wire_indices]
    outer_wires = [wires[o] for o in outside_wire_indices]
    return (outer_wires, inner_wires)


def _mapToCylinder(self, radius: float) -> cq.Wire:
    """Map a closed planar wire to a cylindrical surface"""
    text_flat_edges = self.Edges()
    circumference = 2 * pi * radius

    edges_in = TopTools_HSequenceOfShape()
    wires_out = TopTools_HSequenceOfShape()

    text_cylindrical_edges = []
    for t in text_flat_edges:
        # x,y,z
        t_flat_pts = [t.positionAt(i / 40) for i in range(41)]
        # r,φ,h
        t_polar_pts = [(radius, 2 * pi * p.x / circumference, p.y) for p in t_flat_pts]
        t_cartesian_pts = [
            cq.Vector(p[0] * cos(p[1]), p[0] * sin(p[1]), p[2]) for p in t_polar_pts
        ]
        cylindrical_edge = cq.Edge.makeSplineApprox(t_cartesian_pts)
        text_cylindrical_edges.append(cylindrical_edge)
        edges_in.Append(cylindrical_edge.wrapped)

    ShapeAnalysis_FreeBounds.ConnectEdgesToWires_s(edges_in, 0.0001, False, wires_out)
    wires = [cq.Wire(w) for w in wires_out]
    return wires[0]


cq.Wire.mapToCylinder = _mapToCylinder


def makeTextWires(
    text: str,
    size: float,
    font: str = "Arial",
    fontPath: Optional[str] = None,
    kind: Literal["regular", "bold", "italic"] = "regular",
    halign: Literal["center", "left", "right"] = "center",
    valign: Literal["center", "top", "bottom"] = "center",
) -> list[tuple[list[cq.Wire], list[cq.Wire]]]:
    """Create a list of (outer,inner) wires for each character in text"""

    # Setup to build the flat text
    font_kind = {
        "regular": Font_FA_Regular,
        "bold": Font_FA_Bold,
        "italic": Font_FA_Italic,
    }[kind]

    mgr = Font_FontMgr.GetInstance_s()

    if fontPath and mgr.CheckFont(TCollection_AsciiString(fontPath).ToCString()):
        font_t = Font_SystemFont(TCollection_AsciiString(fontPath))
        font_t.SetFontPath(font_kind, TCollection_AsciiString(fontPath))
        mgr.RegisterFont(font_t, True)

    else:
        font_t = mgr.FindFont(TCollection_AsciiString(font), font_kind)

    builder = Font_BRepTextBuilder()
    font_i = StdPrs_BRepFont(
        NCollection_Utf8String(font_t.FontName().ToCString()),
        font_kind,
        float(size),
    )

    # To determine the position of a character, create a Compound shape for both
    # the substring up to that character and the characer, calculate bounding boxes
    # and store the difference in the x value
    char_face_position = list()
    text_center_offset = Vector()
    for i in range(1, len(text) + 1):
        sub_text = text[:i]
        last_char = sub_text[-1:]
        sub_text_flat = Shape(builder.Perform(font_i, NCollection_Utf8String(sub_text)))
        sub_text_bb = sub_text_flat.BoundingBox()
        last_char_flat = Shape(
            builder.Perform(font_i, NCollection_Utf8String(last_char))
        )
        last_char_bb = last_char_flat.BoundingBox()
        char_face_position.append(
            (last_char_flat, cq.Vector(sub_text_bb.xlen - last_char_bb.xlen, 0, 0))
        )
        if i == len(text) + 1:
            if halign == "center":
                text_center_offset.x = -sub_text_bb.xlen / 2
            elif halign == "right":
                text_center_offset.x = -sub_text_bb.xlen

            if valign == "center":
                text_center_offset.y = -sub_text_bb.ylen / 2
            elif valign == "top":
                text_center_offset.y = -sub_text_bb.ylen

    result = []
    for face, location in char_face_position:
        face_centered = face.translate(text_center_offset + location)
        outer_wires, inner_wires = sortWires(edgesToWires(face_centered.Edges()))
        result.append((outer_wires, inner_wires))

    return result


def _thicken(self, thickness: float) -> cq.Solid:
    """Create a solid from a potentially non planar face by thickening along the normals"""
    solid = BRepOffset_MakeOffset()
    solid.Initialize(
        self.wrapped,
        thickness,
        1.0e-5,
        BRepOffset_Skin,
        False,
        False,
        GeomAbs_Intersection,
        True,
    )
    solid.MakeOffsetShape()
    return cq.Solid(solid.Shape())


cq.Face.thicken = _thicken


def _flipNormal(self) -> int:
    """Checks the direction of the normal of a cylindrical face"""
    position = self.outerWire().positionAt(0)
    normal = self.normalAt()
    # return False if normal.dot(position) > 0 else True
    return 1 if normal.dot(position) > 0 else -1


cq.Face.flipNormal = _flipNormal


def makeTextOnCylinder(
    text: str,
    size: float,
    radius: float,
    thickness: float,
    font: str = "Arial",
    fontPath: Optional[str] = None,
    kind: Literal["regular", "bold", "italic"] = "regular",
    halign: Literal["center", "left", "right"] = "center",
    valign: Literal["center", "top", "bottom"] = "center",
) -> cq.Solid:
    """Create text wrapped around a cylinder"""

    # Create a list of (outside,inside) wires for each letter in text
    text_wire_list = makeTextWires(
        text=text,
        size=size,
        font=font,
        fontPath=fontPath,
        kind=kind,
        halign=halign,
        valign=valign,
    )

    # The character insides need to be removed from the outside but their
    # normals may not be in the same direction as the outside so increase
    # the thickness and thicken the face in both directions
    inside_thickness = min(0.99 * radius, 2 * thickness)
    solid_char_list = []
    # For each character in the text
    for outside_wires, inside_wires in text_wire_list:
        # if inside_wires:
        #     projected_inside_wires = [w.mapToCylinder(radius) for w in inside_wires]
        #     inside_faces = [
        #         cq.Face.makeNSidedSurface(w.Edges(), []) for w in projected_inside_wires
        #     ]
        #     reverse_wire = [f.flipNormal for f in inside_faces]
        #     corrected_projected_inside_wires = []
        #     for i, w in enumerate(projected_inside_wires):
        #         if reverse_wire[i]:
        #             corrected_projected_inside_wires.append(
        #                 cq.Wire(w.wrapped.Reversed())
        #             )
        #         else:
        #             corrected_projected_inside_wires.append(w)

        projected_outside_wires = [w.mapToCylinder(radius) for w in outside_wires]
        # projected_inside_wires = [w.mapToCylinder(radius) for w in inside_wires]
        outside_faces = [
            cq.Face.makeNSidedSurface(w.Edges(), [])
            # for w in projected_outside_wires + corrected_projected_inside_wires
            for w in projected_outside_wires
        ]
        outside_solid = cq.Compound.makeCompound(
            [f.thicken(f.flipNormal() * thickness) for f in outside_faces]
        )
        if inside_wires:
            projected_inside_wires = [w.mapToCylinder(radius) for w in inside_wires]
            inside_faces = [
                cq.Face.makeNSidedSurface(w.Edges(), []) for w in projected_inside_wires
            ]
            # inside_solid = cq.Compound.makeCompound(
            #     [f.thicken(f.flipNormal() * 2 * thickness) for f in inside_faces]
            # )
            inside_solid = cq.Compound.makeCompound(
                [
                    f.thicken(inside_thickness).fuse(f.thicken(-inside_thickness))
                    for f in inside_faces
                ]
            )
            # outside_solid = inside_solid
            outside_solid = outside_solid.cut(inside_solid)
        solid_char_list.append(outside_solid)

    return cq.Compound.makeCompound(solid_char_list)


cyl = cq.Solid.makeCylinder(10, 10)

starttime = timeit.default_timer()
test_text = makeTextOnCylinder(
    "Beingφθ⌀",
    size=10,
    radius=10,
    thickness=1,
    font="Serif",
    fontPath="/usr/share/fonts/truetype/freefont",
)
print(f"The time difference is: {timeit.default_timer() - starttime:0.2f}s")
if "show_object" in locals():
    show_object(test_text, name="test_text")
    show_object(cyl, name="cyl")
