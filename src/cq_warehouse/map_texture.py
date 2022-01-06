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
    GeomAbs_Arc,
)
from OCP.BRepOffsetAPI import BRepOffsetAPI_MakeFilling
from OCP.TopAbs import TopAbs_ShapeEnum, TopAbs_Orientation

FRONT = 0  # Projection results in wires on the front and back of the object
BACK = 1


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


def _isReversed(self) -> bool:
    """Determine if a Face normal is reversed"""
    return self.wrapped.Orientation() == TopAbs_Orientation.TopAbs_REVERSED


cq.Face.isReversed = _isReversed


def _complemented(self) -> cq.Face:
    """Return the Face with its normal flipped"""
    return cq.Face(self.wrapped.Complemented())


cq.Face.complemented = _complemented


def _thicken(self, depth: float, direction: cq.Vector = None) -> cq.Solid:
    """
    Create a solid from a potentially non planar face by thickening along the normals.
    The direction vector can be used to potentially flip the face normal direction such that
    many faces with different normals all go in the same direction (direction need only be
    +/- 90 degrees from the face normal.)
    """

    # Check to see if the normal needs to be flipped
    face_center = self.Center()
    face_normal = self.normalAt(face_center).normalized()
    if not direction is None and face_normal.dot(direction.normalized()) < 0:
        adjusted_depth = -depth
    else:
        adjusted_depth = depth

    solid = BRepOffset_MakeOffset()
    solid.Initialize(
        self.wrapped,
        Offset=adjusted_depth,
        Tol=1.0e-5,
        Mode=BRepOffset_Skin,
        Intersection=True,
        SelfInter=False,
        Join=GeomAbs_Intersection,
        Thickening=True,
        RemoveIntEdges=True,
    )
    solid.MakeOffsetShape()
    return cq.Solid(solid.Shape())


cq.Face.thicken = _thicken


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


def _projectWireToSolid(
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
    front_wires = []
    back_wires = []
    if len(output_wires) > 1:
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
        for i, d in enumerate(output_wires_directions):
            # If wire direction from center of projection aligns with direction
            # (within tolerance) it's considered a "front" wire
            if (d - direction_normalized).Length < 0.00001:
                front_wires.append(output_wires[i])
            else:
                back_wires.append(output_wires[i])
    else:
        front_wires = output_wires
    return (front_wires, back_wires)


cq.Wire.projectToSolid = _projectWireToSolid


def _projectFaceToSolid(
    self: cq.Face,
    solidObject: cq.Solid,
    direction: cq.Vector = None,
    center: cq.Vector = None,
) -> tuple[cq.Face]:
    """
    Project a Face onto a Solid generating new Face on the front and back of the object
    one and only one of `direction` or `center` must be provided
    """
    if not (direction is None) ^ (center is None):
        raise ValueError("Either direction or center must be provided")

    reversed_face = self.wrapped.Orientation() == TopAbs_Orientation.TopAbs_REVERSED

    planar_outer_wire = self.outerWire()
    # if reversed_face:
    #     planar_outer_wire = cq.Wire(planar_outer_wire.wrapped.Complemented())

    (
        projected_front_outer_wires,
        projected_back_outer_wires,
    ) = planar_outer_wire.projectToSolid(solidObject, direction, center)
    planar_inner_wires = self.innerWires()
    projected_front_inner_wires = []
    projected_back_inner_wires = []
    for planar_inner_wire in planar_inner_wires:
        if reversed_face:
            w = cq.Wire(planar_inner_wire.wrapped.Complemented())

        projected_inner_wires = w.projectToSolid(solidObject, direction, center)
        projected_front_inner_wires.extend(projected_inner_wires[FRONT])
        projected_back_inner_wires.extend(projected_inner_wires[BACK])

    if len(projected_front_outer_wires) > 1 or len(projected_back_outer_wires) > 1:
        raise Exception("The projection of this face has broken into fragments")

    front_face = projected_front_outer_wires[0].makeNonPlanarFace(
        interiorWires=projected_front_inner_wires
    )
    # print(f"{self.wrapped.Orientation()=}")
    # print(f"{front_face.wrapped.Orientation()=}")
    # if reversed_face:
    #     print("Reversing face...")
    #     front_face = cq.Face(front_face.wrapped.Complemented())
    # print(f"{front_face.wrapped.Orientation()=}")

    if projected_back_outer_wires:
        back_face = projected_back_outer_wires[0].makeNonPlanarFace(
            interiorWires=projected_back_inner_wires
        )
        # if reversed_face:
        #     back_face = cq.Face(back_face.wrapped.Complemented())
    else:
        back_face = None
    return (front_face, back_face)


cq.Face.projectToSolid = _projectFaceToSolid


def _projectWireToCylinder(self, radius: float) -> cq.Wire:
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


cq.Wire.projectToCylinder = _projectWireToCylinder


def _projectFaceToCylinder(self, radius: float) -> cq.Face:
    """Project the face to a cylinder of the given radius"""

    planar_outer_wire = self.outerWire()
    projected_outer_wire = planar_outer_wire.projectToCylinder(radius)
    planar_inner_wires = self.innerWires()
    projected_inner_wires = [w.projectToCylinder(radius) for w in planar_inner_wires]
    face = projected_outer_wire.makeNonPlanarFace(interiorWires=projected_inner_wires)

    if self.wrapped.Orientation() == TopAbs_Orientation.TopAbs_REVERSED:
        face = cq.Face(face.wrapped.Complemented())

    return face


cq.Face.projectToCylinder = _projectFaceToCylinder

sphere_solid = cq.Solid.makeSphere(50, angleDegrees1=-90)

projection_center = cq.Vector(0, 0, 25)
projection_direction = cq.Vector(0, 1, 0)

arrow = (
    cq.Workplane("XY")
    .circle(1)
    .extrude(25)
    .faces(">Z")
    .workplane()
    .circle(5)
    .workplane(offset=5)
    .circle(0.1)
    .loft()
)
# starttime = timeit.default_timer()

xz_text_faces = (
    cq.Workplane("XZ")
    .text(
        "Beingφθ⌀",
        fontsize=20,
        distance=1,
        font="Serif",
        fontPath="/usr/share/fonts/truetype/freefont",
        halign="center",
    )
    .faces(">Y")
    .vals()
)
# for i, c in enumerate("Beingφθ⌀"):
# print(f"{c} - {xz_text_faces[i].wrapped.Orientation()}")
# print(f"{c} - {xz_text_faces[i].normalAt(xz_text_faces[i].Center())}")

projected_sphere_text_faces = [
    f.projectToSolid(sphere_solid, cq.Vector(0, 1, 0))[BACK] for f in xz_text_faces
]
# for i, c in enumerate("Beingφθ⌀"):
# print(f"{c} - {projected_sphere_text_faces[i].wrapped.Orientation()}")
# print(
#     f"{c} - {projected_sphere_text_faces[i].normalAt(projected_sphere_text_faces[i].Center())}"
# )

projected_sphere_text_solid = cq.Compound.makeCompound(
    [f.thicken(5, direction=cq.Vector(0, -1, 0)) for f in projected_sphere_text_faces]
)
# print(f"The cylindrical time difference is: {timeit.default_timer() - starttime:0.2f}s")

xy_text_faces = (
    cq.Workplane("XY")
    .text(
        "Beingφθ⌀",
        fontsize=20,
        distance=1,
        font="Serif",
        fontPath="/usr/share/fonts/truetype/freefont",
        halign="center",
    )
    .faces("<Z")
    .vals()
)
projected_cylinder_text_faces = [f.projectToCylinder(radius=50) for f in xy_text_faces]
projected_cylinder_text_solid = cq.Compound.makeCompound(
    [f.thicken(5) for f in projected_cylinder_text_faces]
)

square = cq.Workplane("XY").rect(20, 20).extrude(1).faces("<Z").val()
square_projected = square.projectToSolid(sphere_solid, cq.Vector(0, 0, 1))
square_solids = cq.Compound.makeCompound([f.thicken(2) for f in square_projected])
if "show_object" in locals():
    show_object(sphere_solid, name="sphere_solid", options={"alpha": 0.8})
    # show_object(square, name="square")
    # show_object(square_projected[FRONT], name="square_projected front")
    # show_object(square_projected[BACK], name="square_projected back")
    show_object(square_solids, name="square_solids")
    show_object(xz_text_faces, name="text_faces")
    # show_object(projected_sphere_text_faces, name="projected_sphere_text_faces")
    show_object(projected_sphere_text_solid, name="projected_sphere_text_solid")
    # show_object(projected_cylinder_text_faces, name="projected_cylinder_text_faces")
    show_object(
        projected_cylinder_text_solid.rotate(
            cq.Vector(0, 0, 0), cq.Vector(0, 0, 1), 45
        ),
        name="projected_cylinder_text_solid",
    )
    show_object(
        cq.Vertex.makeVertex(*projection_center.toTuple()), name="projection center"
    )
    # show_object(text_conical_projection, name="text_conical_projection")
    # show_object(text_cylindrical_projection, name="text_cylindrical_projection")
