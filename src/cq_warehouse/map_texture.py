from math import pi, sin, cos, sqrt, degrees
from typing import Optional, Literal, Union
from functools import reduce
import cadquery as cq
from cadquery import Vector, Shape
from cadquery.occ_impl.shapes import Face, edgesToWires
from cadquery.cq import T

from OCP.ShapeFix import ShapeFix_Shape, ShapeFix_Solid, ShapeFix_Face
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
from OCP.gp import gp_Pnt, gp_Vec
from OCP.Bnd import Bnd_Box


FRONT = 0  # Projection results in wires on the front and back of the object
BACK = 1


def _getSignedAngle(self, v: "Vector", normal: "Vector" = None) -> float:

    """
    Return the signed angle in RADIANS between two vectors with the given normal
    based on this math:
        angle = atan2((Va x Vb) . Vn, Va . Vb)
    """

    if normal is None:
        gp_normal = gp_Vec(0, 0, -1)
    else:
        gp_normal = normal.wrapped
    return self.wrapped.AngleWithRef(v.wrapped, gp_normal)


cq.Vector.getSignedAngle = _getSignedAngle


def _toLocalCoords(self, obj):
    """Project the provided coordinates onto this plane

    :param obj: an object or vector to convert
    :type vector: a vector or shape
    :return: an object of the same type, but converted to local coordinates

    Most of the time, the z-coordinate returned will be zero, because most
    operations based on a plane are all 2D. Occasionally, though, 3D
    points outside of the current plane are transformed. One such example is
    :py:meth:`Workplane.box`, where 3D corners of a box are transformed to
    orient the box in space correctly.

    """
    # from .shapes import Shape

    if isinstance(obj, Vector):
        return obj.transform(self.fG)
    elif isinstance(obj, Shape):
        return obj.transformShape(self.fG)
    elif isinstance(obj, cq.BoundBox):
        global_bottom_left = Vector(obj.xmin, obj.ymin, obj.zmin)
        global_top_right = Vector(obj.xmax, obj.ymax, obj.zmax)
        local_bottom_left = global_bottom_left.transform(self.fG)
        local_top_right = global_top_right.transform(self.fG)
        local_bbox = Bnd_Box(
            gp_Pnt(*local_bottom_left.toTuple()), gp_Pnt(*local_top_right.toTuple())
        )
        return cq.BoundBox(local_bbox)
    else:
        raise ValueError(
            f"Don't know how to convert type {type(obj)} to local coordinates"
        )


cq.Plane.toLocalCoords = _toLocalCoords


def textOnPath(
    self: T,
    txt: str,
    fontsize: float,
    distance: float,
    start: float = 0.0,
    cut: bool = True,
    combine: bool = False,
    clean: bool = True,
    font: str = "Arial",
    fontPath: Optional[str] = None,
    kind: Literal["regular", "bold", "italic"] = "regular",
) -> T:
    """
    Returns 3D text with the baseline following the given path.

    :param txt: text to be rendered
    :param fontsize: size of the font in model units
    :param distance: the distance to extrude or cut, normal to the workplane plane
    :type distance: float, negative means opposite the normal direction
    :param start: the relative location on path to start the text
    :type start: float, values must be between 0.0 and 1.0
    :param cut: True to cut the resulting solid from the parent solids if found
    :param combine: True to combine the resulting solid with parent solids if found
    :param clean: call :py:meth:`clean` afterwards to have a clean shape
    :param font: font name
    :param fontPath: path to font file
    :param kind: font type
    :return: a CQ object with the resulting solid selected

    The returned object is always a Workplane object, and depends on whether combine is True, and
    whether a context solid is already defined:

    *  if combine is False, the new value is pushed onto the stack.
    *  if combine is true, the value is combined with the context solid if it exists,
       and the resulting solid becomes the new context solid.

    Examples::

        fox = (
            cq.Workplane("XZ")
            .threePointArc((50, 30), (100, 0))
            .textOnPath(
                txt="The quick brown fox jumped over the lazy dog",
                fontsize=5,
                distance=1,
                start=0.1,
            )
        )

        clover = (
            cq.Workplane("front")
            .moveTo(0, 10)
            .radiusArc((10, 0), 7.5)
            .radiusArc((0, -10), 7.5)
            .radiusArc((-10, 0), 7.5)
            .radiusArc((0, 10), 7.5)
            .consolidateWires()
            .textOnPath(
                txt=".x" * 102,
                fontsize=1,
                distance=1,
            )
        )
    """

    def position_face(orig_face: cq.Face) -> cq.Face:
        """
        Reposition a face to the provided path

        Local coordinates are used to calculate the position of the face
        relative to the path. Global coordinates to position the face.
        """
        bbox = self.plane.toLocalCoords(orig_face.BoundingBox())
        face_bottom_center = cq.Vector((bbox.xmin + bbox.xmax) / 2, 0, 0)
        relative_position_on_wire = start + face_bottom_center.x / path_length
        wire_tangent = path.tangentAt(relative_position_on_wire)
        wire_angle = degrees(
            self.plane.xDir.getSignedAngle(wire_tangent, self.plane.zDir)
        )
        wire_position = path.positionAt(relative_position_on_wire)
        global_face_bottom_center = self.plane.toWorldCoords(face_bottom_center)
        return orig_face.translate(wire_position - global_face_bottom_center).rotate(
            wire_position,
            wire_position + self.plane.zDir,
            wire_angle,
        )

    # The top edge or wire on the stack defines the path
    if not self.ctx.pendingWires and not self.ctx.pendingEdges:
        raise Exception("A pending edge or wire must be present to define the path")
    if self.ctx.pendingEdges:
        path = self.ctx.pendingEdges.pop()
    else:
        path = self.ctx.pendingWires.pop()

    # Create text on the current workplane
    raw_text = cq.Compound.makeText(
        txt,
        fontsize,
        distance,
        font=font,
        fontPath=fontPath,
        kind=kind,
        halign="left",
        valign="bottom",
        position=self.plane,
    )
    # Extract just the faces on the workplane
    text_faces = (
        cq.Workplane(raw_text)
        .faces(cq.DirectionMinMaxSelector(self.plane.zDir, False))
        .vals()
    )
    path_length = path.Length()

    # Reposition all of the text faces and re-create 3D text
    faces_on_path = [position_face(f) for f in text_faces]
    result = cq.Compound.makeCompound(
        [cq.Solid.extrudeLinear(f, self.plane.zDir) for f in faces_on_path]
    )
    if cut:
        new_solid = self._cutFromBase(result)
    elif combine:
        new_solid = self._combineWithBase(result)
    else:
        new_solid = self.newObject([result])
    if clean:
        new_solid = new_solid.clean()
    return new_solid


cq.Workplane.textOnPath = textOnPath


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
    adjusted_depth = depth
    if direction is not None:
        face_center = self.Center()
        face_normal = self.normalAt(face_center).normalized()
        if face_normal.dot(direction.normalized()) < 0:
            adjusted_depth = -depth

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
    result = cq.Solid(solid.Shape())
    # if depth != adjusted_depth:
    #     print("flipping")
    #     debug(result)

    return result


cq.Face.thicken = _thicken


def _thicken(self, depth: float, direction: cq.Vector = None):
    """Find all of the faces on the stack and make them Solid objects by thickening along the normals"""
    return self.newObject([f.thicken(depth, direction) for f in self.faces().vals()])


cq.Workplane.thicken = _thicken


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

    To avoid flipping the normal of a face built with the projected wire the orientation
    of the output wires are forced to be the same as self.
    """
    if not (direction is None) ^ (center is None):
        raise ValueError("One of either direction or center must be provided")

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

    target_orientation = self.wrapped.Orientation()

    # Generate a list of the projected wires with aligned orientation
    output_wires = []
    while projection_object.More():
        projected_wire = projection_object.Current()
        if target_orientation == projected_wire.Orientation():
            output_wires.append(cq.Wire(projected_wire))
        else:
            output_wires.append(cq.Wire(projected_wire.Reversed()))
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
            direction_normalized = (center - projection_center).normalized()
        for i, d in enumerate(output_wires_directions):
            # If wire direction from center of projection aligns with direction
            # it's considered a "front" wire
            if d.dot(direction_normalized) > 0:
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
        raise ValueError("One of either direction or center must be provided")

    planar_outer_wire = self.outerWire()
    planar_outer_wire_orientation = planar_outer_wire.wrapped.Orientation()
    (
        projected_front_outer_wires,
        projected_back_outer_wires,
    ) = planar_outer_wire.projectToSolid(solidObject, direction, center)

    planar_inner_wires = [
        w
        if w.wrapped.Orientation() != planar_outer_wire_orientation
        else cq.Wire(w.wrapped.Reversed())
        for w in self.innerWires()
    ]

    projected_front_inner_wires = []
    projected_back_inner_wires = []
    for planar_inner_wire in planar_inner_wires:
        projected_inner_wires = planar_inner_wire.projectToSolid(
            solidObject, direction, center
        )
        projected_front_inner_wires.extend(projected_inner_wires[FRONT])
        projected_back_inner_wires.extend(projected_inner_wires[BACK])

    if len(projected_front_outer_wires) > 1 or len(projected_back_outer_wires) > 1:
        raise Exception("The projection of this face has broken into fragments")

    front_face = projected_front_outer_wires[0].makeNonPlanarFace(
        interiorWires=projected_front_inner_wires
    )

    if projected_back_outer_wires:
        back_face = projected_back_outer_wires[0].makeNonPlanarFace(
            interiorWires=projected_back_inner_wires
        )
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


def _alignToPoints(self, startPoint: cq.Vector, endPoint: cq.Vector):
    """
    Position the zAxis of the given object to the vector defined by the start and end points

    To avoid undesirable rotations about the Z-axis when aligning objects in directions near
    opposite to their original position, calculations are done for both rotating from Y and Z
    and the smaller of these two rotations are used.
    """
    if (endPoint - startPoint).x == 0 and (endPoint - startPoint).y == 0:
        result = self
    else:
        yAxis = cq.Vector(0, 1, 0)
        zAxis = cq.Vector(0, 0, 1)

        # Create a normalized vector from the cq start and end vertices
        targetVector = (endPoint - startPoint).normalized()

        # Calculate the axis of rotation and the amount of rotation required
        rotateAxisZ = targetVector.cross(zAxis)
        rotateAngleZ = -degrees(targetVector.getAngle(zAxis))
        rotateAxisY = targetVector.cross(yAxis)
        rotateAngleY = -degrees(targetVector.getAngle(yAxis))

        # Rotate the object to align with vector and translate to startPoint
        if abs(rotateAngleZ) < abs(rotateAngleY):
            result = self.rotate((0, 0, 0), rotateAxisZ, rotateAngleZ).translate(
                startPoint
            )
        else:
            # Align with Y first then rotate into position
            result = (
                self.rotate((0, 0, 0), (1, 0, 0), -90)
                .rotate((0, 0, 0), rotateAxisY, rotateAngleY)
                .translate(startPoint)
            )

    return result


cq.Workplane.alignToPoints = _alignToPoints

cq.Face.alignToPoints = _alignToPoints


def _faceOnSolid(self, path: cq.Wire, start: float, solid_object: cq.Solid) -> cq.Face:
    """Reposition a face from alignment to the x-axis to the provided path"""
    path_length = path.Length()

    bbox = self.BoundingBox()
    face_bottom_center = cq.Vector((bbox.xmin + bbox.xmax) / 2, 0, 0)
    relative_position_on_path = start + face_bottom_center.x / path_length
    position_on_solid = path.positionAt(relative_position_on_path)
    face_normal = solid_object.normalAt(position_on_solid)

    face_to_project_on = self.alignToPoints(
        startPoint=position_on_solid, endPoint=position_on_solid + face_normal
    )

    projected_face = face_to_project_on.projectToSolid(solid_object, face_normal)[FRONT]

    return projected_face


cq.Face.faceOnSolid = _faceOnSolid


def textOnSolid(
    txt: str,
    fontsize: float,
    distance: float,
    path: cq.Wire,
    start: float,
    solid_object: cq.Solid,
) -> cq.Solid:
    """Create 3D text with a baseline following the given path"""
    linear_faces = (
        cq.Workplane("XY")
        .text(
            txt=txt,
            fontsize=fontsize,
            distance=distance,
            halign="left",
            valign="bottom",
        )
        .faces("<Z")
        .vals()
    )

    faces_on_path = [f.faceOnSolid(path, start, solid_object) for f in linear_faces]
    solids_on_path = [f.thicken(distance) for f in faces_on_path]

    return cq.Compound.makeCompound(solids_on_path)
