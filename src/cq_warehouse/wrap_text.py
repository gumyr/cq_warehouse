from math import pi, sin, cos, sqrt
import cadquery as cq
from cadquery import Vector, Shape
from typing import Optional, Literal, Union
from cadquery.occ_impl.shapes import edgesToWires
import timeit
from functools import reduce

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
    Creates a hexagon array of points and pushes them onto the stack.
    If you want to position the array at another point, create another workplane
    that is shifted to the position you would like to use as a reference

    :param diagonal: tip to tip size of hexagon ( must be > 0)
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


def createWireRelationships(
    wires: list[cq.Wire],
) -> tuple[list[cq.Wire], list[cq.Wire]]:
    """
    Create a dictionary of exterior/interior wire relationships
        {exterior wire: [wires interior to exterior wire,]}
    such that faces (potentially projected onto a surface) can be reconstructed:
    """
    faces_from_wires = [cq.Face.makeFromWires(w, []) for w in wires]
    area_of_wires = [f.Area() for f in faces_from_wires]
    inside_wire_indices = []
    used_wires = []
    wire_relationships = {}
    for o, f_outer in enumerate(faces_from_wires):
        if o in inside_wire_indices:
            continue
        for i, f_inner in enumerate(faces_from_wires):
            if o == i or i in inside_wire_indices:
                continue
            if f_outer.cut(f_inner).Area() < area_of_wires[o]:
                inside_wire_indices.append(i)
                used_wires.append(wires[o])
                used_wires.append(wires[i])
                if wires[o] in wire_relationships:
                    wire_relationships[wires[o]].append(wires[i])
                else:
                    wire_relationships[wires[o]] = [wires[i]]

    # Find all the missing wires and add them as external only
    for w in wires:
        if w not in used_wires:
            wire_relationships[w] = []

    return wire_relationships


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
) -> list[dict[cq.Wire : list[cq.Wire]]]:
    """
    Create a list of dictionaries with exterior/interior wire relationships such that faces
    (potentially projected onto a surface) can be reconstructed:
    - list of characters in the text string (one or more)
        {exterior wire: [wires interior to exterior wire,]}
    """

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
        wire_relationships = createWireRelationships(
            edgesToWires(face_centered.Edges())
        )
        result.append(wire_relationships)

    return result


def _thicken(self, depth: float) -> cq.Solid:
    """Create a solid from a potentially non planar face by thickening along the normals"""
    solid = BRepOffset_MakeOffset()
    solid.Initialize(
        self.wrapped,
        depth,
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
    self: cq.Wire,
    solidObject: cq.Solid,
    direction: cq.Vector = None,
    center: cq.Vector = None,
) -> tuple[list[cq.Wire]]:
    """
    Project a Wire onto a Solid generating new Wires on the front and back of the object
    one and only one of `direction` or `center` must be provided

    Generates two lists of wires, one for the front and one for the back
    """
    if not (direction is None) ^ (center is None):
        raise ValueError("Either direction or center must be provided")

    if not direction is None:
        projection_object = BRepProj_Projection(
            self.wrapped,
            cq.Shape.cast(solidObject.wrapped).wrapped,
            gp_Dir(*direction.toTuple()),
        )
    else:
        projection_object = BRepProj_Projection(
            self.wrapped,
            cq.Shape.cast(solidObject.wrapped).wrapped,
            gp_Pnt(*center.toTuple()),
        )
    # Generate a list of the projected wires
    output_wires = []
    while projection_object.More():
        output_wires.append(cq.Wire(projection_object.Current()))
        projection_object.Next()

    # BRepProj_Projection is inconsistent in the order that it returns projected
    # wires, sometimes front first and sometimes back - so sort this out
    output_wires_centers = [w.Center() for w in output_wires]
    projection_center = reduce(
        lambda v0, v1: v0 + v1, output_wires_centers, cq.Vector(0, 0, 0)
    ) * (1.0 / len(output_wires_centers))
    output_wires_directions = [
        (w - projection_center).normalized() for w in output_wires_centers
    ]
    if not direction is None:
        direction_normalized = direction.normalized()
    else:
        direction_normalized = (projection_center - center).normalized()
    front_wires = []
    back_wires = []
    for i, d in enumerate(output_wires_directions):
        # If wire direction from center of projection aligns with direction
        # (within tolerance) it's considered a "front" wire
        if (d - direction_normalized).Length < 0.00001:
            front_wires.append(output_wires[i])
        else:
            back_wires.append(output_wires[i])
    return (front_wires, back_wires)


cq.Wire.projectWireOnSolid = _projectWireOnSolid


def __makeNonPlanarFace(
    exterior: Union[cq.Wire, list[cq.Edge]],
    surfacePoints: list[cq.Vector] = None,
    interiorWires: list[cq.Wire] = None,
) -> cq.Face:
    """Create a potentially non-planar face bounded by exterior (wire or edges),
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
    surface_face = cq.Face(surface.Shape())
    if not surface_face.isValid():
        raise ValueError("Unable to build face from exterior")

    # Next, add wires that define interior holes - note these wires must be entirely interior
    if interiorWires:
        makeface_object = BRepBuilderAPI_MakeFace(surface_face.wrapped)
        for w in interiorWires:
            makeface_object.Add(w.wrapped)
        surface_face = cq.Face(makeface_object.Face()).fix()
        if not surface_face.isValid():
            raise ValueError("interiorWires must be completely within exterior")

    return surface_face


def _makeNonPlanarFace(
    self,
    surfacePoints: list[cq.Vector] = None,
    interiorWires: list[cq.Wire] = None,
) -> cq.Face:
    return __makeNonPlanarFace(self, surfacePoints, interiorWires)


cq.Wire.makeNonPlanarFace = _makeNonPlanarFace


def projectTextOnSolid(
    text: str,
    size: float,
    depth: float,
    solidObject: cq.Solid,
    direction: cq.Vector = None,
    center: cq.Vector = None,
    font: str = "Arial",
    fontPath: Optional[str] = None,
    kind: Literal["regular", "bold", "italic"] = "regular",
    halign: Literal["center", "left", "right"] = "center",
    valign: Literal["center", "top", "bottom"] = "center",
) -> cq.Compound:
    """Create text projected onto the given Solid object"""

    if not (direction is None) ^ (center is None):
        raise ValueError("Either direction or center must be provided")

    FRONT = 0  # Projection results in wires on the front and back of the object - just need the front

    # Create a list of the character wire dictionary structure - one for each letter in the text
    character_wire_dicts = makeTextWires(
        text=text,
        size=size,
        font=font,
        fontPath=fontPath,
        kind=kind,
        halign=halign,
        valign=valign,
    )

    character_solids = []
    # For each character in the text project the wires in the dictionary
    # and create non-planar faces from them - possibly with holes
    # for the interiors of the characters
    for c, wire_relationships in enumerate(character_wire_dicts):
        for exterior_wire, interior_wires in wire_relationships.items():
            if not direction is None:
                projected_exterior_wire_list = exterior_wire.projectWireOnSolid(
                    solidObject, direction=direction
                )[FRONT]
            else:
                projected_exterior_wire_list = exterior_wire.projectWireOnSolid(
                    solidObject, center=center
                )[FRONT]
            if len(projected_exterior_wire_list) > 1:
                raise Exception(
                    f"The projection of character '{text[c]}' has broken into fragments"
                )
            projected_interior_wires = []
            if interior_wires:
                projected_interior_wires = []
                for interior_wire in interior_wires:
                    if not direction is None:
                        projected_interior_wires.extend(
                            interior_wire.projectWireOnSolid(
                                solidObject, direction=direction
                            )[FRONT]
                        )
                    else:
                        projected_interior_wires.extend(
                            interior_wire.projectWireOnSolid(
                                solidObject, center=center
                            )[FRONT]
                        )

            exterior_face = projected_exterior_wire_list[0].makeNonPlanarFace(
                interiorWires=projected_interior_wires
            )
            exterior_solid = exterior_face.thicken(depth)
            character_solids.append(exterior_solid)

    return cq.Compound.makeCompound(character_solids)


sphere_solid = cq.Solid.makeSphere(50, angleDegrees1=-90)

starttime = timeit.default_timer()
test_text = projectTextOnSolid(
    "Beingφθ⌀",
    # "i",
    size=10,
    depth=1,
    solidObject=sphere_solid,
    direction=cq.Vector(0, 0, 1),
    # center=cq.Vector(0, 0, 0),
    font="Serif",
    fontPath="/usr/share/fonts/truetype/freefont",
    halign="center",
)
print(f"The time difference is: {timeit.default_timer() - starttime:0.2f}s")

# letter_wire_dictionary = makeTextWires("e", 10)[0]
# print(len(letter_wire_dictionary))
# outer_e = list(letter_wire_dictionary.keys())[0]
# inner_e = letter_wire_dictionary[outer_e][0]
# projected_outer_e = outer_e.projectWireOnSolid(sphere_solid, cq.Vector(0, 0, 1))[0][0]
# projected_inner_e = inner_e.projectWireOnSolid(sphere_solid, cq.Vector(0, 0, 1))[0][0]
# e_face = projected_outer_e.makeNonPlanarFace(interiorWires=[projected_inner_e])
# e_solid = e_face.thicken(1)

if "show_object" in locals():
    show_object(test_text, name="test_text")
    # show_object(sphere_solid, name="sphere_solid")
    # show_object(projected_outer_e, name="projected_outer_e")
    # show_object(projected_inner_e, name="projected_inner_e")
    # show_object(outer_e, name="outer_e")
    # show_object(inner_e, name="inner_e")
    # show_object(e_face, name="e_face")
    # show_object(e_solid, name="e_solid")
