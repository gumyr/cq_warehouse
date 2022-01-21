"""
Cadquery Extensions

name: extensions.py
by:   Gumyr
date: August 2nd 2021

desc:

    This python module provides extensions to the native cadquery code base.
    Hopefully future generations of cadquery will incorporate this or similar
    functionality.

todo:
    Instead of assuming embossed edges/wires/faces are on the XY plane, transform to local XY plane

license:

    Copyright 2022 Gumyr

    Licensed under the Apache License, Version 2.0 (the "License");
    you may not use this file except in compliance with the License.
    You may obtain a copy of the License at

        http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS,
    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    See the License for the specific language governing permissions and
    limitations under the License.

"""
import sys
import logging
from math import pi, sin, cos, radians, sqrt, degrees
from typing import Optional, Literal, Union, Tuple
import cadquery as cq
from cadquery.occ_impl.shapes import VectorLike
from cadquery.cq import T

from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
from OCP.ShapeAnalysis import ShapeAnalysis_FreeBounds
from OCP.TopTools import TopTools_HSequenceOfShape
from OCP.BRepOffset import BRepOffset_MakeOffset, BRepOffset_Skin, BRepOffset_RectoVerso
from OCP.BRepProj import BRepProj_Projection
from OCP.gp import gp_Pnt, gp_Dir
from OCP.gce import gce_MakeLin
from OCP.GeomAbs import (
    GeomAbs_C0,
    GeomAbs_Intersection,
    GeomAbs_Intersection,
)
from OCP.BRepOffsetAPI import BRepOffsetAPI_MakeFilling
from OCP.TopAbs import TopAbs_Orientation
from OCP.gp import gp_Pnt, gp_Vec
from OCP.Bnd import Bnd_Box
from OCP.StdFail import StdFail_NotDone
from OCP.Standard import Standard_NoSuchObject
from OCP.BRepIntCurveSurface import BRepIntCurveSurface_Inter

# Logging configuration - uncomment to enable logs
# logging.basicConfig(
#     filename="cq_warehouse.log",
#     encoding="utf-8",
#     level=logging.DEBUG,
#     format="%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)s - %(funcName)20s() ] - %(message)s",
# )

"""

Assembly extensions: rotate(), translate()

"""


def _translate(self, vec: VectorLike):
    """
    Moves the current assembly (without making a copy) by the specified translation vector
    :param vec: The translation vector
    """
    self.loc = self.loc * cq.Location(cq.Vector(vec))
    return self


cq.Assembly.translate = _translate


def _rotate(self, axis: VectorLike, angle: float):
    """
    Rotates the current assembly (without making a copy) around the axis of rotation
    by the specified angle

    :param axis: The axis of rotation (starting at the origin)
    :type axis: a 3-tuple of floats
    :param angle: the rotation angle, in degrees
    :type angle: float
    """
    self.loc = self.loc * cq.Location(cq.Vector(0, 0, 0), cq.Vector(axis), angle)
    return self


cq.Assembly.rotate = _rotate

"""

Plane extensions: toLocalCoords()

"""


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

    if isinstance(obj, cq.Vector):
        return obj.transform(self.fG)
    elif isinstance(obj, cq.Shape):
        return obj.transformShape(self.fG)
    elif isinstance(obj, cq.BoundBox):
        global_bottom_left = cq.Vector(obj.xmin, obj.ymin, obj.zmin)
        global_top_right = cq.Vector(obj.xmax, obj.ymax, obj.zmax)
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


"""

Vector extensions: rotateX(), rotateY(), rotateZ(), pointToVector(), toVertex(), getSignedAngle()

"""


def _vector_rotate_x(self, angle: float) -> cq.Vector:
    """cq.Vector rotate angle in degrees about x-axis"""
    return cq.Vector(
        self.x,
        self.y * cos(radians(angle)) - self.z * sin(radians(angle)),
        self.y * sin(radians(angle)) + self.z * cos(radians(angle)),
    )


cq.Vector.rotateX = _vector_rotate_x


def _vector_rotate_y(self, angle: float) -> cq.Vector:
    """cq.Vector rotate angle in degrees about y-axis"""
    return cq.Vector(
        self.x * cos(radians(angle)) + self.z * sin(radians(angle)),
        self.y,
        -self.x * sin(radians(angle)) + self.z * cos(radians(angle)),
    )


cq.Vector.rotateY = _vector_rotate_y


def _vector_rotate_z(self, angle: float) -> cq.Vector:
    """cq.Vector rotate angle in degrees about z-axis"""
    return cq.Vector(
        self.x * cos(radians(angle)) - self.y * sin(radians(angle)),
        self.x * sin(radians(angle)) + self.y * cos(radians(angle)),
        self.z,
    )


cq.Vector.rotateZ = _vector_rotate_z


def _point_to_vector(self, plane: str, offset: float = 0.0) -> cq.Vector:
    """map a 2D point on the XY plane to 3D space on the given plane at the offset"""
    if not isinstance(plane, str) or plane not in ["XY", "XZ", "YZ"]:
        raise ValueError("plane " + str(plane) + " must be one of: XY,XZ,YZ")
    if plane == "XY":
        mapped_point = cq.Vector(self.x, self.y, offset)
    elif plane == "XZ":
        mapped_point = cq.Vector(self.x, offset, self.y)
    else:  # YZ
        mapped_point = cq.Vector(offset, self.x, self.y)
    return mapped_point


cq.Vector.pointToVector = _point_to_vector


def _toVertex(self):
    """Convert a Vector to a Vertex"""
    return cq.Vertex.makeVertex(*self.toTuple())


cq.Vector.toVertex = _toVertex


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


"""

Vertex extensions: __add__(), __sub__(), __str__()

"""


def __vertex_add__(
    self, other: Union[cq.Vertex, cq.Vector, Tuple[float, float, float]]
) -> cq.Vertex:
    """Add a Vector or tuple of floats to a Vertex"""
    if isinstance(other, cq.Vertex):
        new_vertex = cq.Vertex.makeVertex(
            self.X + other.X, self.Y + other.Y, self.Z + other.Z
        )
    elif isinstance(other, (cq.Vector, tuple)):
        new_other = cq.Vector(other)
        new_vertex = cq.Vertex.makeVertex(
            self.X + new_other.x, self.Y + new_other.y, self.Z + new_other.z
        )
    else:
        raise TypeError(
            "Vertex addition only supports Vertex,Vector or tuple(float,float,float) as input"
        )
    return new_vertex


cq.Vertex.__add__ = __vertex_add__


def __vertex_sub__(self, other: Union[cq.Vertex, cq.Vector, tuple]) -> cq.Vertex:
    """Subtract a Vector or tuple of floats to a Vertex"""
    if isinstance(other, cq.Vertex):
        new_vertex = cq.Vertex.makeVertex(
            self.X - other.X, self.Y - other.Y, self.Z - other.Z
        )
    elif isinstance(other, (cq.Vector, tuple)):
        new_other = cq.Vector(other)
        new_vertex = cq.Vertex.makeVertex(
            self.X - new_other.x, self.Y - new_other.y, self.Z - new_other.z
        )
    else:
        raise TypeError(
            "Vertex subtraction only supports Vertex,Vector or tuple(float,float,float) as input"
        )
    return new_vertex


cq.Vertex.__sub__ = __vertex_sub__


def __vertex_str__(self) -> str:
    """Display a Vertex"""
    return f"Vertex: ({self.X}, {self.Y}, {self.Z})"


cq.Vertex.__str__ = __vertex_str__


def _vertex_to_vector(self) -> cq.Vector:
    """Convert a Vertex to a Vector"""
    return cq.Vector(self.toTuple())


cq.Vertex.toVector = _vertex_to_vector


"""

Workplane extensions: textOnPath(), hexArray(), thicken()

"""


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
    valign: Literal["center", "top", "bottom"] = "center",
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
    for stack_object in self.vals():
        if type(stack_object) == cq.Edge:
            path = self.ctx.pendingEdges.pop(0)
            break
        if type(stack_object) == cq.Wire:
            path = self.ctx.pendingWires.pop(0)
            break

    # Create text on the current workplane
    raw_text = cq.Compound.makeText(
        txt,
        fontsize,
        distance,
        font=font,
        fontPath=fontPath,
        kind=kind,
        halign="left",
        valign=valign,
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
            lpoints.append(cq.Vector(xSpacing * x, ySpacing * y + ySpacing / 2))
    for x in range(1, xCount, 2):
        for y in range(yCount):
            lpoints.append(cq.Vector(xSpacing * x, ySpacing * y + ySpacing))

    # shift points down and left relative to origin if requested
    offset = cq.Vector()
    if center[0]:
        offset += cq.Vector(-xSpacing * (xCount - 1) * 0.5, 0)
    if center[1]:
        offset += cq.Vector(0, -ySpacing * (yCount - 1) * 0.5)
    lpoints = [x + offset for x in lpoints]

    return self.pushPoints(lpoints)


cq.Workplane.hexArray = _hexArray


def _workplaneThicken(self, depth: float, direction: cq.Vector = None):
    """Find all of the faces on the stack and make them Solid objects by thickening along the normals"""
    return self.newObject([f.thicken(depth, direction) for f in self.faces().vals()])


cq.Workplane.thicken = _workplaneThicken


"""

Face extensions: thicken(), projectToShape(), embossToShape()

"""


def _faceThicken(self, depth: float, direction: cq.Vector = None) -> cq.Solid:
    """
    Create a solid from a potentially non planar face by thickening along the normals.
    The direction vector can be used to indicate which way is 'up', potentially flipping the
    face normal direction such that many faces with different normals all go in the same
    direction (direction need only be +/- 90 degrees from the face normal.)
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
        # BRepOffset_RectoVerso - which describes the offset of a given surface shell along both
        # sides of the surface but doesn't seem to work
        Intersection=True,
        SelfInter=False,
        Join=GeomAbs_Intersection,  # Could be GeomAbs_Arc,GeomAbs_Tangent,GeomAbs_Intersection
        Thickening=True,
        RemoveIntEdges=True,
    )
    solid.MakeOffsetShape()
    try:
        result = cq.Solid(solid.Shape())
    except StdFail_NotDone as e:
        raise RuntimeError("Error applying thicken to given Face") from e

    return result


cq.Face.thicken = _faceThicken


def _projectFaceToShape(
    self: cq.Face,
    targetObject: cq.Shape,
    direction: VectorLike = None,
    center: VectorLike = None,
    internalFacePoints: list[cq.Vector] = [],
) -> list[cq.Face]:
    """
    Project a Face onto a Solid generating new Face on the surfaces of the object
    one and only one of `direction` or `center` must be provided.

    There are four phase to creation of the projected face:
    1- extract the outer wire and project
    2- extract the inner wires and project
    3- extract surface points within the outer wire
    4- build a non planar face
    """

    if not (direction is None) ^ (center is None):
        raise ValueError("One of either direction or center must be provided")
    if direction is not None:
        direction_vector = cq.Vector(direction)
        center_point = None
    else:
        direction_vector = None
        center_point = cq.Vector(center)

    # Phase 1 - outer wire
    planar_outer_wire = self.outerWire()
    planar_outer_wire_orientation = planar_outer_wire.wrapped.Orientation()
    projected_outer_wires = planar_outer_wire.projectToShape(
        targetObject, direction_vector, center_point
    )
    logging.debug(
        f"projecting outerwire resulted in {len(projected_outer_wires)} wires"
    )
    # Phase 2 - inner wires
    planar_inner_wire_list = [
        w
        if w.wrapped.Orientation() != planar_outer_wire_orientation
        else cq.Wire(w.wrapped.Reversed())
        for w in self.innerWires()
    ]
    # Project inner wires on to potentially multiple surfaces
    projected_inner_wire_list = [
        w.projectToShape(targetObject, direction_vector, center_point)
        for w in planar_inner_wire_list
    ]
    # Need to transpose this list so it's organized by surface then inner wires
    projected_inner_wire_list = [list(x) for x in zip(*projected_inner_wire_list)]

    for i in range(len(planar_inner_wire_list)):
        logging.debug(
            f"projecting innerwire resulted in {len(projected_inner_wire_list[i])} wires"
        )
    # Ensure the length of the list is the same as that of the outer wires
    projected_inner_wire_list.extend(
        [[] for _ in range(len(projected_outer_wires) - len(projected_inner_wire_list))]
    )

    # Phase 3 - Find points on the surface by projecting a "grid" composed of internalFacePoints

    # Not sure if it's always a good idea to add an internal central point so the next
    # two lines of code can be easily removed without impacting the rest
    if not internalFacePoints:
        internalFacePoints = [planar_outer_wire.Center()]

    if not internalFacePoints:
        projected_grid_points = []
    else:
        if len(internalFacePoints) == 1:
            planar_grid = cq.Edge.makeLine(
                planar_outer_wire.positionAt(0), internalFacePoints[0]
            )
        else:
            planar_grid = cq.Wire.makePolygon(
                [cq.Vector(v) for v in internalFacePoints]
            )
        projected_grids = planar_grid.projectToShape(
            targetObject, direction_vector, center_point
        )
        projected_grid_points = [
            [cq.Vector(*v.toTuple()) for v in grid.Vertices()]
            for grid in projected_grids
        ]
    logging.debug(f"projecting grid resulted in {len(projected_grid_points)} points")

    # Phase 4 - Build the faces
    projected_faces = [
        ow.makeNonPlanarFace(
            surfacePoints=projected_grid_points[i],
            interiorWires=projected_inner_wire_list[i],
        )
        for i, ow in enumerate(projected_outer_wires)
    ]

    return projected_faces


cq.Face.projectToShape = _projectFaceToShape


def _embossFaceToShape(
    self: cq.Face,
    targetObject: cq.Shape,
    surfacePoint: VectorLike,
    surfaceXDirection: VectorLike,
    internalFacePoints: list[cq.Vector] = [],
) -> cq.Face:
    """
    Wrap a Face onto a Shape

    There are four phase to creation of the projected face:
    1- extract the outer wire and project
    2- extract the inner wires and project
    3- extract surface points within the outer wire
    4- build a non planar face
    """

    # Phase 1 - outer wire
    planar_outer_wire = self.outerWire()
    planar_outer_wire_orientation = planar_outer_wire.wrapped.Orientation()
    embossed_outer_wire = planar_outer_wire.embossToShape(
        targetObject, surfacePoint, surfaceXDirection
    )

    # Phase 2 - inner wires
    planar_inner_wires = [
        w
        if w.wrapped.Orientation() != planar_outer_wire_orientation
        else cq.Wire(w.wrapped.Reversed())
        for w in self.innerWires()
    ]
    embossed_inner_wires = [
        w.embossToShape(targetObject, surfacePoint, surfaceXDirection)
        for w in planar_inner_wires
    ]

    # Phase 3 - Find points on the surface by projecting a "grid" composed of internalFacePoints

    # Not sure if it's always a good idea to add an internal central point so the next
    # two lines of code can be easily removed without impacting the rest
    if not internalFacePoints:
        internalFacePoints = [planar_outer_wire.Center()]

    if not internalFacePoints:
        embossed_surface_points = []
    else:
        if len(internalFacePoints) == 1:
            planar_grid = cq.Edge.makeLine(
                planar_outer_wire.positionAt(0), internalFacePoints[0]
            )
        else:
            planar_grid = cq.Wire.makePolygon(
                [cq.Vector(v) for v in internalFacePoints]
            )

        embossed_grid = planar_grid.embossToShape(
            targetObject, surfacePoint, surfaceXDirection
        )
        embossed_surface_points = [
            cq.Vector(*v.toTuple()) for v in embossed_grid.Vertices()
        ]

    # Phase 4 - Build the faces
    embossed_face = embossed_outer_wire.makeNonPlanarFace(
        surfacePoints=embossed_surface_points, interiorWires=embossed_inner_wires
    )

    return embossed_face


cq.Face.embossToShape = _embossFaceToShape
"""

Wire extensions:

"""


def makeNonPlanarFace(
    exterior: Union[cq.Wire, list[cq.Edge]],
    surfacePoints: list[VectorLike] = None,
    interiorWires: list[cq.Wire] = None,
) -> cq.Face:
    """Create a potentially non-planar face bounded by exterior (wire or edges),
    optionally refined by surfacePoints with optional holes defined by interiorWires"""

    surface_points = [cq.Vector(p) for p in surfacePoints]

    # First, create the non-planar surface
    surface = BRepOffsetAPI_MakeFilling(
        Degree=3,  # the order of energy criterion to minimize for computing the deformation of the surface
        NbPtsOnCur=15,  # average number of points for discretisation of the edges
        NbIter=2,
        Anisotropie=False,
        Tol2d=0.00001,  # the maximum distance allowed between the support surface and the constraints
        Tol3d=0.0001,  # the maximum distance allowed between the support surface and the constraints
        TolAng=0.01,  # the maximum angle allowed between the normal of the surface and the constraints
        TolCurv=0.1,  # the maximum difference of curvature allowed between the surface and the constraint
        MaxDeg=8,  # the highest degree which the polynomial defining the filling surface can have
        MaxSegments=9,  # the greatest number of segments which the filling surface can have
    )
    if isinstance(exterior, cq.Wire):
        outside_edges = exterior.Edges()
    else:
        outside_edges = [e.Edge() for e in exterior]
    for edge in outside_edges:
        surface.Add(edge.wrapped, GeomAbs_C0)

    try:
        surface.Build()
        surface_face = cq.Face(surface.Shape())
    except (StdFail_NotDone, Standard_NoSuchObject) as e:
        raise RuntimeError(
            "Error building non-planar face with provided exterior"
        ) from e
    if surface_points:
        for pt in surface_points:
            surface.Add(gp_Pnt(*pt.toTuple()))
        try:
            surface.Build()
            surface_face = cq.Face(surface.Shape())
        except StdFail_NotDone as e:
            raise RuntimeError(
                "Error building non-planar face with provided surfacePoints"
            ) from e

    # Next, add wires that define interior holes - note these wires must be entirely interior
    if interiorWires:
        makeface_object = BRepBuilderAPI_MakeFace(surface_face.wrapped)
        for w in interiorWires:
            makeface_object.Add(w.wrapped)
        try:
            surface_face = cq.Face(makeface_object.Face())
        except StdFail_NotDone as e:
            raise RuntimeError(
                "Error adding interior hole in non-planar face with provided interiorWires"
            ) from e

    surface_face = surface_face.fix()
    if not surface_face.isValid():
        raise RuntimeError("non planar face is invalid")

    return surface_face


def _makeNonPlanarFace(
    self,
    surfacePoints: list[cq.Vector] = None,
    interiorWires: list[cq.Wire] = None,
) -> cq.Face:
    return makeNonPlanarFace(self, surfacePoints, interiorWires)


cq.Wire.makeNonPlanarFace = _makeNonPlanarFace

"""

Wire extensions: projectToShape(), embossToShape()

"""


def _projectWireToShape(
    self: Union[cq.Wire, cq.Edge],
    targetObject: cq.Shape,
    direction: VectorLike = None,
    center: VectorLike = None,
) -> list[cq.Wire]:
    """
    Project a Wire onto a Solid generating new Wires on the surfaces of the object
    one and only one of `direction` or `center` must be provided. Note that one more
    more wires may be generated depending on the topology of the target object and
    location/direction of projection.

    To avoid flipping the normal of a face built with the projected wire the orientation
    of the output wires are forced to be the same as self.
    """
    if not (direction is None) ^ (center is None):
        raise ValueError("One of either direction or center must be provided")
    if direction is not None:
        direction_vector = cq.Vector(direction).normalized()
        center_point = None
    else:
        direction_vector = None
        center_point = cq.Vector(center)

    # Project the wire on the target object
    if not direction_vector is None:
        projection_object = BRepProj_Projection(
            self.wrapped,
            cq.Shape.cast(targetObject.wrapped).wrapped,
            gp_Dir(*direction_vector.toTuple()),
        )
    else:
        projection_object = BRepProj_Projection(
            self.wrapped,
            cq.Shape.cast(targetObject.wrapped).wrapped,
            gp_Pnt(*center_point.toTuple()),
        )

    # Generate a list of the projected wires with aligned orientation
    output_wires = []
    target_orientation = self.wrapped.Orientation()
    while projection_object.More():
        projected_wire = projection_object.Current()
        if target_orientation == projected_wire.Orientation():
            output_wires.append(cq.Wire(projected_wire))
        else:
            output_wires.append(cq.Wire(projected_wire.Reversed()))
        projection_object.Next()

    logging.debug(f"wire generated {len(output_wires)} projected wires")

    # BRepProj_Projection is inconsistent in the order that it returns projected
    # wires, sometimes front first and sometimes back - so sort this out by sorting
    # by distance from the original planar wire
    if len(output_wires) > 1:
        output_wires_distances = []
        planar_wire_center = self.Center()
        for output_wire in output_wires:
            output_wire_center = output_wire.Center()
            if direction_vector is not None:
                output_wire_direction = (
                    output_wire_center - planar_wire_center
                ).normalized()
                if output_wire_direction.dot(direction_vector) >= 0:
                    output_wires_distances.append(
                        (
                            output_wire,
                            (output_wire_center - planar_wire_center).Length,
                        )
                    )
            else:
                output_wires_distances.append(
                    (output_wire, (output_wire_center - center_point).Length)
                )

        output_wires_distances.sort(key=lambda x: x[1])
        logging.debug(
            f"projected, filtered and sorted wire list is of length {len(output_wires_distances)}"
        )
        output_wires = [w[0] for w in output_wires_distances]

    return output_wires


cq.Wire.projectToShape = _projectWireToShape


def _embossWireToShape(
    self: cq.Edge,
    targetObject: cq.Shape,
    surfacePoint: VectorLike,
    surfaceXDirection: VectorLike,
    tolerance: float = 0.001,
) -> cq.Wire:
    """Emboss a planar Wire to targetObject maintaining the length while doing so"""

    planar_edges = self.Edges()
    planar_closed = self.IsClosed()
    logging.debug(f"embossing wire with {len(planar_edges)} edges")
    edges_in = TopTools_HSequenceOfShape()
    wires_out = TopTools_HSequenceOfShape()

    # Need to keep track of the separation between adjacent edges
    first_start_point = None
    last_end_point = None
    edge_separatons = []
    surface_point = cq.Vector(surfacePoint)
    surface_x_direction = cq.Vector(surfaceXDirection)

    # If the wire doesn't start at the origin, create an embossed construction line to get
    # to the beginning of the first edge
    if planar_edges[0].positionAt(0) == cq.Vector(0, 0, 0):
        edge_surface_point = surface_point
        planar_edge_end_point = cq.Vector(0, 0, 0)
    else:
        construction_line = cq.Edge.makeLine(
            cq.Vector(0, 0, 0), planar_edges[0].positionAt(0)
        )
        embossed_construction_line = construction_line.embossToShape(
            targetObject, surface_point, surface_x_direction, tolerance
        )
        edge_surface_point = embossed_construction_line.positionAt(1)
        planar_edge_end_point = planar_edges[0].positionAt(0)

    # Emboss each edge and add them to the wire builder
    for planar_edge in planar_edges:
        local_planar_edge = planar_edge.translate(-planar_edge_end_point)
        embossed_edge = local_planar_edge.embossToShape(
            targetObject, edge_surface_point, surface_x_direction, tolerance
        )
        edge_surface_point = embossed_edge.positionAt(1)
        planar_edge_end_point = planar_edge.positionAt(1)
        if first_start_point is None:
            first_start_point = embossed_edge.positionAt(0)
            first_edge = embossed_edge
        edges_in.Append(embossed_edge.wrapped)
        if last_end_point is not None:
            edge_separatons.append(
                (embossed_edge.positionAt(0) - last_end_point).Length
            )
        last_end_point = embossed_edge.positionAt(1)

    # Set the tolerance of edge connection to more than the worst case edge separation
    # max_edge_separation = max(edge_separatons)
    closure_gap = (last_end_point - first_start_point).Length
    logging.debug(f"embossed wire closure gap {closure_gap:0.3f}")
    if planar_closed and closure_gap > tolerance:
        logging.debug(f"closing gap in embossed wire of size {closure_gap}")
        gap_edge = cq.Edge.makeSpline(
            [last_end_point, first_start_point],
            tangents=[embossed_edge.tangentAt(1), first_edge.tangentAt(0)],
        )
        edges_in.Append(gap_edge.wrapped)

    ShapeAnalysis_FreeBounds.ConnectEdgesToWires_s(
        edges_in,
        tolerance,
        False,
        wires_out,
    )
    # Note: wires_out is an OCP.TopTools.TopTools_HSequenceOfShape not a simple list
    embossed_wires = [w for w in wires_out]
    embossed_wire = cq.Wire(embossed_wires[0])

    if planar_closed and not embossed_wire.IsClosed():
        embossed_wire.close()
        logging.debug(
            f"embossed wire was not closed, did fixing succeed: {embossed_wire.IsClosed()}"
        )

    embossed_wire = embossed_wire.fix()

    if not embossed_wire.isValid():
        raise RuntimeError("embossed wire is not valid")

    return embossed_wire


cq.Wire.embossToShape = _embossWireToShape

"""

Edge extensions: projectToShape(), embossToShape()

"""
cq.Edge.projectToShape = _projectWireToShape


def _embossEdgeToShape(
    self: cq.Edge,
    targetObject: cq.Shape,
    surfacePoint: VectorLike,
    surfaceXDirection: VectorLike,
    tolerance: float = 0.01,
) -> cq.Edge:
    """
    Emboss a planar Edge to targetObject while maintaining edge length

    Algorithm - piecewise approximation of points on surface -> generate spline:

    - successively increasing the number of points to emboss
        - create local plane at current point given surface normal and surface x direction
        - create new approximate point on local plane from next planar point
        - get global position of next approximate point
        - using current normal and next approximate point find next surface intersection point and normal
    - create spline from points
    - measure length of spline
    - repeat with more points unless within target tolerance

    """

    def find_point_on_surface(
        current_surface_point: cq.Vector,
        current_surface_normal: cq.Vector,
        planar_relative_position: cq.Vector,
    ) -> cq.Vector:
        """
        Given a 2D relative position from a surface point, find the closest point on the surface.
        """
        segment_plane = cq.Plane(
            origin=current_surface_point,
            xDir=surface_x_direction,
            normal=current_surface_normal,
        )
        target_point = segment_plane.toWorldCoords(planar_relative_position.toTuple())
        (next_surface_point, next_surface_normal) = targetObject.findIntersection(
            point=target_point, direction=target_point - target_object_center
        )[0]
        return (next_surface_point, next_surface_normal)

    surface_x_direction = cq.Vector(surfaceXDirection)

    planar_edge_length = self.Length()
    planar_edge_closed = self.IsClosed()
    target_object_center = targetObject.Center()
    loop_count = 0
    subdivisions = 2
    length_error = sys.float_info.max

    while length_error > tolerance and loop_count < 8:

        # Initialize the algorithm by priming it with the start of Edge self
        surface_origin = cq.Vector(surfacePoint)
        (surface_origin_point, surface_origin_normal) = targetObject.findIntersection(
            point=surface_origin,
            direction=surface_origin - target_object_center,
        )[0]
        planar_relative_position = self.positionAt(0)
        (current_surface_point, current_surface_normal) = find_point_on_surface(
            surface_origin_point,
            surface_origin_normal,
            planar_relative_position,
        )
        embossed_edge_points = [current_surface_point]

        # Loop through all of the subdivisions calculating surface points
        for div in range(1, subdivisions + 1):
            planar_relative_position = self.positionAt(
                div / subdivisions
            ) - self.positionAt((div - 1) / subdivisions)
            (current_surface_point, current_surface_normal) = find_point_on_surface(
                current_surface_point,
                current_surface_normal,
                planar_relative_position,
            )
            embossed_edge_points.append(current_surface_point)

        # Create a spline through the points and determine length difference from target
        embossed_edge = cq.Edge.makeSpline(
            embossed_edge_points, periodic=planar_edge_closed
        )
        length_error = planar_edge_length - embossed_edge.Length()
        loop_count = loop_count + 1
        subdivisions = subdivisions * 2

    if length_error > tolerance:
        raise RuntimeError(
            f"Length error of {length_error} exceeds requested tolerance {tolerance}"
        )
    if not embossed_edge.isValid():
        raise RuntimeError("embossed edge invalid")

    return embossed_edge


cq.Edge.embossToShape = _embossEdgeToShape

"""

Shape extensions: findIntersection(), projectText(), embossText()

"""


def _findIntersection(
    self: cq.Shape, point: cq.Vector, direction: cq.Vector
) -> list[tuple[cq.Vector, cq.Vector]]:
    """Return both the point(s) and normal(s) of the intersection of the line and the shape"""

    oc_point = gp_Pnt(*point.toTuple())
    oc_axis = gp_Dir(*direction.toTuple())
    oc_shape = self.wrapped

    intersection_line = gce_MakeLin(oc_point, oc_axis).Value()
    intersectMaker = BRepIntCurveSurface_Inter()
    intersectMaker.Init(oc_shape, intersection_line, 0.0001)

    intersections = []
    while intersectMaker.More():
        interPt = intersectMaker.Pnt()
        distance = oc_point.Distance(interPt)
        intersections.append(
            (cq.Face(intersectMaker.Face()), cq.Vector(interPt), distance)
        )
        intersectMaker.Next()

    intersections.sort(key=lambda x: x[2])
    intersecting_faces = [i[0] for i in intersections]
    intersecting_points = [i[1] for i in intersections]
    intersecting_normals = [
        f.normalAt(intersecting_points[i]).normalized()
        for i, f in enumerate(intersecting_faces)
    ]
    result = []
    for i in range(len(intersecting_points)):
        result.append((intersecting_points[i], intersecting_normals[i]))

    return result


cq.Shape.findIntersection = _findIntersection


def _projectText(
    self,
    txt: str,
    fontsize: float,
    depth: float,
    path: Union[cq.Wire, cq.Edge],
    font: str = "Arial",
    fontPath: Optional[str] = None,
    kind: Literal["regular", "bold", "italic"] = "regular",
    valign: Literal["center", "top", "bottom"] = "center",
    start: float = 0,
) -> cq.Compound:
    """Create 3D text with a baseline following the given path on Shape"""

    path_length = path.Length()
    shape_center = self.Center()

    # Create text faces
    text_faces = (
        cq.Workplane("XY")
        .text(
            txt,
            fontsize,
            1,
            font=font,
            fontPath=fontPath,
            kind=kind,
            halign="left",
            valign=valign,
        )
        .faces("<Z")
        .vals()
    )
    logging.debug(f"projecting text sting '{txt}' as {len(text_faces)} face(s)")

    # Position each text face normal to the surface along the path and project to the surface
    projected_faces = []
    for text_face in text_faces:
        bbox = text_face.BoundingBox()
        face_center_x = (bbox.xmin + bbox.xmax) / 2
        relative_position_on_wire = start + face_center_x / path_length
        path_position = path.positionAt(relative_position_on_wire)
        path_tangent = path.tangentAt(relative_position_on_wire)
        (surface_point, surface_normal) = self.findIntersection(
            path_position,
            path_position - shape_center,
        )[0]
        surface_normal_plane = cq.Plane(
            origin=surface_point, xDir=path_tangent, normal=surface_normal
        )
        projection_face = text_face.translate((-face_center_x, 0, 0)).transformShape(
            surface_normal_plane.rG
        )
        logging.debug(f"projecting face at {relative_position_on_wire=:0.2f}")
        projected_faces.append(
            projection_face.projectToShape(self, surface_normal * -1)[0]
        )

    # Assume that the user just want faces if depth is zero
    if depth == 0:
        projected_text = projected_faces
    else:
        projected_text = [
            f.thicken(depth, f.Center() - shape_center) for f in projected_faces
        ]

    logging.debug(f"finished projecting text sting '{txt}'")

    return cq.Compound.makeCompound(projected_text)


cq.Shape.projectText = _projectText


def _embossText(
    self,
    txt: str,
    fontsize: float,
    depth: float,
    path: Union[cq.Wire, cq.Edge],
    font: str = "Arial",
    fontPath: Optional[str] = None,
    kind: Literal["regular", "bold", "italic"] = "regular",
    valign: Literal["center", "top", "bottom"] = "center",
    start: float = 0,
) -> cq.Compound:
    """Create 3D text with a baseline following the given path on Shape"""

    path_length = path.Length()
    shape_center = self.Center()

    # Create text faces
    text_faces = (
        cq.Workplane("XY")
        .text(
            txt,
            fontsize,
            1,
            font=font,
            fontPath=fontPath,
            kind=kind,
            halign="left",
            valign=valign,
        )
        .faces("<Z")
        .vals()
    )

    logging.debug(f"embossing text sting '{txt}' as {len(text_faces)} face(s)")

    # Determine the distance along the path to position the face and emboss around shape
    embossed_faces = []
    for text_face in text_faces:
        bbox = text_face.BoundingBox()
        face_center_x = (bbox.xmin + bbox.xmax) / 2
        relative_position_on_wire = start + face_center_x / path_length
        path_position = path.positionAt(relative_position_on_wire)
        path_tangent = path.tangentAt(relative_position_on_wire)
        logging.debug(f"embossing face at {relative_position_on_wire=:0.2f}")
        embossed_faces.append(
            text_face.translate((-face_center_x, 0, 0)).embossToShape(
                self, path_position, path_tangent
            )
        )

    # Assume that the user just want faces if depth is zero
    if depth == 0:
        embossed_text = embossed_faces
    else:
        embossed_text = [
            f.thicken(depth, f.Center() - shape_center) for f in embossed_faces
        ]

    logging.debug(f"finished embossing text sting '{txt}'")

    return cq.Compound.makeCompound(embossed_text)


cq.Shape.embossText = _embossText
