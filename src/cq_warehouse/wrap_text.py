from math import pi, sin, cos, sqrt
import cadquery as cq
from cadquery import Vector, Shape
from typing import Optional, Literal, Union
from cadquery.occ_impl.shapes import edgesToWires
import timeit

from OCP.Font import (
    Font_FontMgr,
    Font_FA_Regular,
    Font_FA_Italic,
    Font_FA_Bold,
    Font_SystemFont,
)
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
from OCP.TCollection import TCollection_AsciiString
from OCP.StdPrs import StdPrs_BRepFont, StdPrs_BRepTextBuilder as Font_BRepTextBuilder
from OCP.NCollection import NCollection_Utf8String
from OCP.ShapeAnalysis import ShapeAnalysis_FreeBounds
from OCP.TopTools import TopTools_HSequenceOfShape
from OCP.BRepOffset import BRepOffset_MakeOffset, BRepOffset_Skin
from OCP.BRepProj import BRepProj_Projection
from OCP.gp import gp_Pnt, gp_Dir
from OCP.GeomAbs import (
    GeomAbs_Shape,
    GeomAbs_C0,
    GeomAbs_Intersection,
    GeomAbs_JoinType,
)
from OCP.BRepOffsetAPI import BRepOffsetAPI_MakeFilling


def _hexArray(
    self,
    diagonal: float,
    xCount: int,
    yCount: int,
    center: Union[bool, tuple[bool, bool]] = True,
):
    """
    Creates an array of points and pushes them onto the stack.
    If you want to position the array at another point, create another workplane
    that is shifted to the position you would like to use as a reference

    :param xSpacing: spacing between points in the x direction ( must be > 0)
    :param ySpacing: spacing between points in the y direction ( must be > 0)
    :param xCount: number of points ( > 0 )
    :param yCount: number of points ( > 0 )
    :param center: If True, the array will be centered around the workplane center.
      If False, the lower corner will be on the reference point and the array will
      extend in the positive x and y directions. Can also use a 2-tuple to specify
      centering along each axis.
    """
    xSpacing = 3 * diagonal / 4
    ySpacing = diagonal * sqrt(3) / 2
    if xSpacing <= 0 or ySpacing <= 0 or xCount < 1 or yCount < 1:
        raise ValueError("Spacing and count must be > 0 ")

    if isinstance(center, bool):
        center = (center, center)

    lpoints = []  # coordinates relative to bottom left point
    for x in range(0, xCount, 2):
        for y in range(yCount):
            lpoints.append(Vector(xSpacing * x, ySpacing * y + ySpacing / 2))
    for x in range(1, xCount, 2):
        for y in range(yCount):
            lpoints.append(Vector(xSpacing * x, ySpacing * y + ySpacing))

    # shift points down and left relative to origin if requested
    offset = Vector()
    if center[0]:
        offset += Vector(-xSpacing * (xCount - 1) * 0.5, 0)
    if center[1]:
        offset += Vector(0, -ySpacing * (yCount - 1) * 0.5)
    lpoints = [x + offset for x in lpoints]

    return self.pushPoints(lpoints)


cq.Workplane.hexArray = _hexArray


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
    position = self.wrapped.outerWire().positionAt(0)
    normal = self.normalAt()
    return 1 if normal.dot(position) > 0 else -1


cq.Face.flipNormal = _flipNormal


def _projectWireOnSolid(
    self: cq.Wire, solid_object: cq.Solid, direction: cq.Vector
) -> list[cq.Wire]:
    projection_object = BRepProj_Projection(
        self.wrapped,
        cq.Shape.cast(solid_object.wrapped).wrapped,
        gp_Dir(*direction.toTuple()),
    )
    # A Compound could be generated but it seems less useful
    # output_wires = projection_object.Shape()

    # Generate a list of the projected wires
    output_wires = []
    while projection_object.More():
        output_wires.append(cq.Wire(projection_object.Current()))
        projection_object.Next()

    return output_wires


cq.Wire.projectWireOnSolid = _projectWireOnSolid


def makeNonPlanarFace(
    exterior: Union[cq.Wire, list[cq.Edge]],
    surfacePoints: list[cq.Vector] = None,
    interiorWires: list[cq.Wire] = None,
) -> cq.Face:
    """Create a potentally non-planar face bounded by exterior (wire or edges),
    optionally refined by surfacePoints with optional holes defined by interiorWires"""

    # First, create the non-planar surface
    surface = BRepOffsetAPI_MakeFilling(
        Degree=3,
        NbPtsOnCur=15,
        NbIter=2,
        Anisotropie=False,
        Tol2d=0.00001,
        Tol3d=0.0001,
        TolAng=0.01,
        TolCurv=0.1,
        MaxDeg=8,
        MaxSegments=9,
    )
    if isinstance(exterior, cq.Wire):
        outside_edges = exterior.Edges()
    else:
        outside_edges = [e.Edge() for e in exterior]
    for edge in outside_edges:
        surface.Add(edge.wrapped, GeomAbs_C0)
    if surfacePoints:
        for pt in surfacePoints:
            surface.Add(gp_Pnt(*pt.toTuple()))
    surface.Build()

    # Next, add wires that define interior holes - note these wires must be entirely interior

    # surface_face = cq.Face(surface.Shape()).fix()
    surface_face = cq.Face(surface.Shape())
    if interiorWires:
        makeface_object = BRepBuilderAPI_MakeFace(surface_face.wrapped)
        for w in interiorWires:
            makeface_object.Add(w.wrapped)
        surface_face = cq.Face(makeface_object.Face()).fix()
    return surface_face


def makeTextOnSolid(
    text: str,
    size: float,
    thickness: float,
    solid_object: cq.Solid,
    direction: cq.Vector,
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

    solid_char_list = []
    # For each character in the text
    for outside_wires, inside_wires in text_wire_list:
        projected_outside_wires = []
        for w in outside_wires:
            projected_outside_wires.extend(
                w.projectWireOnSolid(solid_object, direction)
            )
        if inside_wires:
            projected_inside_wires = []
            for w in inside_wires:
                projected_inside_wires.extend(
                    w.projectWireOnSolid(solid_object, direction)
                )
        outside_faces = [
            makeNonPlanarFace(w, interiorWires=projected_inside_wires)
            for w in projected_outside_wires
        ]
        print(f"{type(outside_faces[0])=}")
        # outside_solid = cq.Compound.makeCompound(
        #     # [f.thicken(f.flipNormal() * thickness) for f in outside_faces]
        #     [f.thicken(thickness) for f in outside_faces]
        # )

        # if inside_wires:
        #     projected_inside_wires = []
        #     for w in inside_wires:
        #         projected_inside_wires.extend(
        #             w.projectWireOnSolid(solid_object, direction)
        #         )
        #     all_edges = []
        #     for w in projected_outside_wires:
        #         all_edges.extend(w.Edges())
        #     for w in projected_inside_wires:
        #         all_edges.extend(w.Edges())
        #     face = cq.Face.makeNSidedSurface(all_edges, [])
        # inside_faces = [
        #     cq.Face.makeNSidedSurface(w.Edges(), []) for w in projected_inside_wires
        # ]
        # inside_solid = cq.Compound.makeCompound(
        #     [
        #         f.thicken(inside_thickness).fuse(f.thicken(-inside_thickness))
        #         for f in inside_faces
        #     ]
        # )
        # # outside_solid = inside_solid
        # outside_solid = outside_solid.cut(inside_solid)
        # solid_char_list.append(outside_solid)
    return outside_faces[1]
    # return cq.Compound.makeCompound(solid_char_list)


sphere_solid = cq.Solid.makeSphere(50, angleDegrees1=-90)

# starttime = timeit.default_timer()
# test_text = makeTextOnSolid(
#     # "Beingφθ⌀",
#     "e",
#     size=10,
#     thickness=1,
#     solid_object=sphere_solid,
#     direction=cq.Vector(0, 0, 1),
#     font="Serif",
#     fontPath="/usr/share/fonts/truetype/freefont",
#     halign="center",
# )
# print(f"The time difference is: {timeit.default_timer() - starttime:0.2f}s")

(outer_e, inner_e) = makeTextWires("e", 10)[0]
print(type(outer_e[0]))
print(type(inner_e), len(inner_e), type(inner_e[0]))
e_face_outer = makeNonPlanarFace(outer_e[0])
e_face_inner = makeNonPlanarFace(inner_e[0])
e_face = makeNonPlanarFace(outer_e[0], interiorWires=inner_e)
e_solid = e_face.thicken(1)
# r = 10
# cyl = cq.Solid.makeCylinder(r, 40)
# starttime = timeit.default_timer()
# c = 2 * pi * r
# d = 4 * (c / 10) / 3
# pattern_wires = (
#     cq.Workplane("XY")
#     .hexArray(d, 10, 5, center=(True, False))
#     .polygon(6, 0.8 * d)
#     .wires()
#     .vals()
# )
# mapped_wires = [w.mapToCylinder(r) for w in pattern_wires]
# mapped_faces = [cq.Face.makeNSidedSurface(w.Edges(), []) for w in mapped_wires]
# pos_pattern = cq.Compound.makeCompound(
#     [f.thicken(f.flipNormal() * 1) for f in mapped_faces]
# )
# pos_patterned_cylinder = cyl.fuse(pos_pattern, glue=True)
# print(f"The time difference is: {timeit.default_timer() - starttime:0.2f}s")

if "show_object" in locals():
    # show_object(test_text, name="test_text")
    # show_object(sphere_solid, name="sphere_solid")
    # show_object(cyl, name="cyl")
    # show_object(pattern_wires, name="pattern_wires")
    # show_object(mapped_wires, name="mapped_wires")
    # show_object(pos_pattern, name="pos_pattern")
    # show_object(pos_patterned_cylinder, name="pos_patterned_cylinder")
    show_object(outer_e, name="outer_e")
    show_object(inner_e, name="inner_e")
    show_object(e_face_outer, name="e_face_outer")
    show_object(e_face_inner, name="e_face_inner")
    show_object(e_face, name="e_face")
    show_object(e_solid, name="e_solid")
