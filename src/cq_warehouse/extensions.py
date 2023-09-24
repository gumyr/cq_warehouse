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
import copy
import logging
import math
import random
from itertools import combinations
from enum import Enum, auto
from functools import reduce
from typing import Optional, Literal, Union, Tuple, Iterable
from types import MethodType
import cadquery as cq
from cadquery.occ_impl.shapes import VectorLike, fix, downcast, shapetype
from cadquery.cq import T
from cadquery.hull import find_hull
from cadquery import (
    Assembly,
    BoundBox,
    Compound,
    Edge,
    Face,
    Plane,
    Location,
    Shape,
    Solid,
    Sketch,
    Vector,
    Vertex,
    Wire,
    Workplane,
    DirectionMinMaxSelector,
    Color,
)
from cadquery.sketch import Modes, Point
from cq_warehouse.fastener import (
    Screw,
    Nut,
    Washer,
    DomedCapNut,
    HexNut,
    UnchamferedHexagonNut,
    SquareNut,
)
from cq_warehouse.bearing import Bearing
from cq_warehouse.thread import IsoThread

from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
from OCP.ShapeAnalysis import ShapeAnalysis_FreeBounds
from OCP.TopTools import TopTools_HSequenceOfShape
from OCP.BRepOffset import BRepOffset_MakeOffset, BRepOffset_Skin, BRepOffset_RectoVerso
from OCP.BRepProj import BRepProj_Projection
from OCP.gce import gce_MakeLin
from OCP.GeomAbs import (
    GeomAbs_C0,
    GeomAbs_Intersection,
    GeomAbs_Intersection,
)
from OCP.BRepOffsetAPI import BRepOffsetAPI_MakeFilling
from OCP.TopAbs import TopAbs_Orientation
from OCP.Bnd import Bnd_Box
from OCP.StdFail import StdFail_NotDone
from OCP.Standard import Standard_NoSuchObject
from OCP.BRepIntCurveSurface import BRepIntCurveSurface_Inter
from OCP.gp import gp_Vec, gp_Pnt, gp_Ax1, gp_Dir, gp_Trsf, gp, gp_GTrsf
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
from OCP.BRepBuilderAPI import BRepBuilderAPI_Transform, BRepBuilderAPI_Copy
from OCP.ShapeUpgrade import ShapeUpgrade_UnifySameDomain

# Logging configuration - all cq_warehouse logs are level DEBUG or WARNING
# logging.basicConfig(
#     filename="cq_warehouse.log",
#     encoding="utf-8",
#     # level=logging.DEBUG,
#     level=logging.CRITICAL,
#     format="%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)s - %(funcName)20s() ] - %(message)s",
# )
logging.getLogger("cq_warehouse").addHandler(logging.NullHandler())
logger = logging.getLogger("cq_warehouse")

"""

Assembly extensions: rotate(), translate(), fastenerQuantities(), fastenerLocations(), findLocation(),
                    doObjectsIntersect(), areObjectsValid(), section()

"""


def _assembly_translate(self, vec: "VectorLike") -> "Assembly":
    """
    Moves the current assembly (without making a copy) by the specified translation vector

    Args:
        vec: The translation vector

    Returns:
        The translated Assembly

    Example:
        car_assembly.translate((1,2,3))
    """
    self.loc = self.loc * Location(Vector(vec))
    return self


Assembly.translate = _assembly_translate


def _assembly_rotate(self, axis: "VectorLike", angle: float) -> "Assembly":
    """Rotate Assembly

    Rotates the current assembly (without making a copy) around the axis of rotation
    by the specified angle

    Args:
        axis: The axis of rotation (starting at the origin)
        angle: The rotation angle, in degrees

    Returns:
        The rotated Assembly

    Example:
        car_assembly.rotate((0,0,1),90)
    """
    self.loc = self.loc * Location(Vector(0, 0, 0), Vector(axis), angle)
    return self


Assembly.rotate = _assembly_rotate


def _fastener_quantities(self, bom: bool = True, deep: bool = True) -> dict:
    """Fastener Quantities

    Generate a bill of materials of the fasteners in an assembly augmented by the hole methods
    bom: returns fastener.info if True else counts fastener instances

    Args:
        bom (bool, optional): Select a Bill of Materials or raw fastener instance count. Defaults to True.
        deep (bool, optional): Scan the entire Assembly. Defaults to True.

    Returns:
        fastener usage summary
    """
    from cq_warehouse.fastener import Screw, Nut, Washer
    from cq_warehouse.bearing import Bearing

    assembly_list = []
    if deep:
        for _name, sub_assembly in self.traverse():
            assembly_list.append(sub_assembly)
    else:
        assembly_list.append(self)

    fasteners = []
    for sub_assembly in assembly_list:
        for value in sub_assembly.metadata.values():
            if isinstance(value, (Screw, Nut, Washer, Bearing)):
                fasteners.append(value)

    unique_fasteners = set(fasteners)
    if bom:
        quantities = {f.info: fasteners.count(f) for f in unique_fasteners}
    else:
        quantities = {f: fasteners.count(f) for f in unique_fasteners}
    return quantities


Assembly.fastenerQuantities = _fastener_quantities


def _fastener_locations(self, fastener: Union["Nut", "Screw"]) -> list[Location]:
    """Return location(s) of fastener

    Generate a list of cadquery Locations for the given fastener relative to the Assembly

    Args:
        fastener: fastener to search for

    Returns:
        a list of cadquery Location objects for each fastener instance
    """

    # from functools import reduce

    name_to_fastener = {}
    base_assembly_structure = {}
    # Extract a list of only the fasteners from the metadata
    for name, a in self.traverse():
        base_assembly_structure[name] = a
        # if a.metadata is None:
        #     continue

        for key, value in a.metadata.items():
            if value == fastener:
                name_to_fastener[key] = value

    fastener_path_locations = {}
    base_assembly_path = self._flatten()
    for assembly_path in base_assembly_path.keys():
        for fastener_name in name_to_fastener.keys():
            if fastener_name in assembly_path:
                parents = assembly_path.split("/")
                fastener_path_locations[fastener_name] = [
                    base_assembly_structure[name].loc for name in parents
                ]
    fastener_locations = [
        reduce(lambda l1, l2: l1 * l2, locs)
        for locs in fastener_path_locations.values()
    ]

    return fastener_locations


Assembly.fastenerLocations = _fastener_locations


def _find_Location(self, target: str) -> Location:
    """Find Location of named target

    Return the Location of the target object relative to the given Assembly
    including the given Assembly.

    Args:
        target (str): name of target object

    Raises:
        ValueError: target object not in found in Assembly

    Returns:
        cq.Location: Location of target relative to self
    """
    target_assembly = None
    for object_name, object_assembly in self.objects.items():
        if object_name.split("/")[-1] == target:
            target_assembly = object_assembly
            break

    if target_assembly is None:
        raise ValueError(f"{target} not found in given assembly")

    locations = []
    current_assembly = target_assembly
    while True:
        locations.append(current_assembly.loc)
        current_assembly = current_assembly.parent
        if current_assembly is self or current_assembly is None:
            break

    return reduce(lambda l1, l2: l1 * l2, locations)


Assembly.findLocation = _find_Location


def _doObjectsIntersect(self, tolerance: float = 1e-5) -> bool:
    """Do Objects Intersect

    Determine if any of the objects within an Assembly intersect by
    intersecting each of the shapes with each other and checking for
    a common volume.

    Args:
        self (Assembly): Assembly to test
        tolerance (float, optional): maximum allowable volume difference. Defaults to 1e-5.

    Returns:
        bool: do the object intersect
    """
    shapes = [
        shape.moved(self.findLocation(name))
        if isinstance(shape, Shape)
        else shape.val().moved(self.findLocation(name))
        for name, part in self.traverse()
        for shape in part.shapes
    ]
    shape_index_pairs = [
        tuple(map(int, comb))
        for comb in combinations([i for i in range(len(shapes))], 2)
    ]
    for shape_index_pair in shape_index_pairs:
        common_volume = (
            shapes[shape_index_pair[0]].intersect(shapes[shape_index_pair[1]]).Volume()
        )
        if common_volume > tolerance:
            return True
    return False


Assembly.doObjectsIntersect = _doObjectsIntersect


def _areObjectsValid(self) -> bool:
    """Are Objects Valid

    Check the validity of all the objects in this Assembly

    Returns:
        bool: all objects are valid
    """
    parts = [shape for _name, part in self.traverse() for shape in part.shapes]
    return all(
        [
            part.isValid() if isinstance(part, Shape) else part.val().isValid()
            for part in parts
        ]
    )


Assembly.areObjectsValid = _areObjectsValid


def _crossSection_Assembly(self, plane: "Plane") -> "Assembly":
    """Cross Section

    Generate a 2D slice of an assembly as a colorize Assembly

    Args:
        plane (Plane): the plane with which to slice the Assembly

    Returns:
        Assembly: The cross section assembly with original colors
    """
    plane_as_face = Face.makePlane(basePnt=plane.origin, dir=plane.zDir)

    cross_section = cq.Assembly(None, name=self.name)
    for name, part in self.traverse():
        location = self.findLocation(name)
        for shape in part.shapes:
            cross_section.add(
                shape.located(location).intersect(plane_as_face),
                color=part.color,
                name=name,
            )
    return cross_section


Assembly.section = _crossSection_Assembly

"""

Plane extensions: toLocalCoords(), toWorldCoords()

"""


def __toFromLocalCoords(
    self, obj: Union["VectorLike", "Shape", "BoundBox"], to: bool = True
):
    """Reposition the object relative to this plane

    Args:
        obj: an object, vector, or bounding box to convert
        to: convert `to` or from local coordinates. Defaults to True.

    Returns:
        an object of the same type, but repositioned to local coordinates

    """
    # from .shapes import Shape

    transform_matrix = self.fG if to else self.rG

    if isinstance(obj, (tuple, Vector)):
        return Vector(obj).transform(transform_matrix)
    elif isinstance(obj, Shape):
        return obj.transformShape(transform_matrix)
    elif isinstance(obj, BoundBox):
        global_bottom_left = Vector(obj.xmin, obj.ymin, obj.zmin)
        global_top_right = Vector(obj.xmax, obj.ymax, obj.zmax)
        local_bottom_left = global_bottom_left.transform(transform_matrix)
        local_top_right = global_top_right.transform(transform_matrix)
        local_bbox = Bnd_Box(
            gp_Pnt(*local_bottom_left.toTuple()), gp_Pnt(*local_top_right.toTuple())
        )
        return BoundBox(local_bbox)
    else:
        raise ValueError(
            f"Unable to repositioned type {type(obj)} with respect to local coordinates"
        )


Plane._toFromLocalCoords = __toFromLocalCoords


def _toLocalCoords(self, obj: Union["VectorLike", "Shape", "BoundBox"]):
    """Reposition the object relative to this plane

    Args:
        obj: an object, vector, or bounding box to convert

    Returns:
        an object of the same type, but repositioned to local coordinates

    """
    return self._toFromLocalCoords(obj, True)


Plane.toLocalCoords = _toLocalCoords


def _fromLocalCoords(self, obj: Union[tuple, "Vector", "Shape", "BoundBox"]):
    """Reposition the object relative from this plane

    Args:
        obj: an object, vector, or bounding box to convert

    Returns:
        an object of the same type, but repositioned to world coordinates

    """
    return self._toFromLocalCoords(obj, False)


Plane.fromLocalCoords = _fromLocalCoords

"""

Vector extensions: rotateX(), rotateY(), rotateZ(), toVertex(), getSignedAngle()

"""


def _vector_rotate_x(self, angle: float) -> "Vector":
    """Rotate Vector about X-Axis

    Args:
        angle: Angle in degrees

    Returns:
        Rotated Vector
    """
    return Vector(
        gp_Vec(self.x, self.y, self.z).Rotated(gp.OX_s(), math.pi * angle / 180)
    )


Vector.rotateX = _vector_rotate_x


def _vector_rotate_y(self, angle: float) -> "Vector":
    """Rotate Vector about Y-Axis

    Args:
        angle: Angle in degrees

    Returns:
        Rotated Vector
    """
    return Vector(
        gp_Vec(self.x, self.y, self.z).Rotated(gp.OY_s(), math.pi * angle / 180)
    )


Vector.rotateY = _vector_rotate_y


def _vector_rotate_z(self, angle: float) -> "Vector":
    """Rotate Vector about Z-Axis

    Args:
        angle: Angle in degrees

    Returns:
        Rotated Vector
    """
    return Vector(
        gp_Vec(self.x, self.y, self.z).Rotated(gp.OZ_s(), math.pi * angle / 180)
    )


Vector.rotateZ = _vector_rotate_z


def _vector_to_vertex(self) -> "Vertex":
    """Convert to Vector to Vertex

    Returns:
        Vertex equivalent of Vector
    """
    return Vertex.makeVertex(*self.toTuple())


Vector.toVertex = _vector_to_vertex


def _getSignedAngle(self, v: "Vector", normal: "Vector" = None) -> float:
    """Signed Angle Between Vectors

    Return the signed angle in RADIANS between two vectors with the given normal
    based on this math: angle = atan2((Va × Vb) ⋅ Vn, Va ⋅ Vb)

    Args:
        v: Second Vector.

        normal: Vector's Normal. Defaults to -Z Axis.

    Returns:
        Angle between vectors
    """
    if normal is None:
        gp_normal = gp_Vec(0, 0, -1)
    else:
        gp_normal = normal.wrapped
    # gp_normal = normal.wrapped if normal else gp_Vec(0, 0, -1)
    return self.wrapped.AngleWithRef(v.wrapped, gp_normal)


Vector.getSignedAngle = _getSignedAngle


"""

Vertex extensions: __add__(), __sub__(), __str__(), toVector

"""


def _vertex_add__(
    self, other: Union["Vertex", "Vector", Tuple[float, float, float]]
) -> "Vertex":
    """Add

    Add to a Vertex with a Vertex, Vector or Tuple

    Args:
        other: Value to add

    Raises:
        TypeError: other not in [Tuple,Vector,Vertex]

    Returns:
        Result

    Example:
        part.faces(">Z").vertices("<Y and <X").val() + (0, 0, 15)

        which creates a new Vertex 15mm above one extracted from a part. One can add or
        subtract a cadquery ``Vertex``, ``Vector`` or ``tuple`` of float values to a
        Vertex with the provided extensions.
    """
    if isinstance(other, Vertex):
        new_vertex = Vertex.makeVertex(
            self.X + other.X, self.Y + other.Y, self.Z + other.Z
        )
    elif isinstance(other, (Vector, tuple)):
        new_other = Vector(other)
        new_vertex = Vertex.makeVertex(
            self.X + new_other.x, self.Y + new_other.y, self.Z + new_other.z
        )
    else:
        raise TypeError(
            "Vertex addition only supports Vertex,Vector or tuple(float,float,float) as input"
        )
    return new_vertex


Vertex.__add__ = _vertex_add__


def _vertex_sub__(self, other: Union["Vertex", "Vector", tuple]) -> "Vertex":
    """Subtract

    Substract a Vertex with a Vertex, Vector or Tuple from self

    Args:
        other: Value to add

    Raises:
        TypeError: other not in [Tuple,Vector,Vertex]

    Returns:
        Result

    Example:
        part.faces(">Z").vertices("<Y and <X").val() - Vector(10, 0, 0)
    """
    if isinstance(other, Vertex):
        new_vertex = Vertex.makeVertex(
            self.X - other.X, self.Y - other.Y, self.Z - other.Z
        )
    elif isinstance(other, (Vector, tuple)):
        new_other = Vector(other)
        new_vertex = Vertex.makeVertex(
            self.X - new_other.x, self.Y - new_other.y, self.Z - new_other.z
        )
    else:
        raise TypeError(
            "Vertex subtraction only supports Vertex,Vector or tuple(float,float,float) as input"
        )
    return new_vertex


Vertex.__sub__ = _vertex_sub__


def _vertex_str__(self) -> str:
    """To String

    Convert Vertex to String for display

    Returns:
        Vertex as String
    """
    return f"Vertex: ({self.X}, {self.Y}, {self.Z})"


Vertex.__str__ = _vertex_str__
Vertex.__repr__ = _vertex_str__


def _vertex_to_vector(self) -> "Vector":
    """To Vector

    Convert a Vertex to Vector

    Returns:
        Vector representation of Vertex
    """
    return Vector(self.toTuple())


Vertex.toVector = _vertex_to_vector


"""

Workplane extensions: textOnPath(), hexArray(), thicken(), fastenerHole(), clearanceHole(),
                      tapHole(), threadedHole(), pushFastenerLocations(), makeFingerJoints()

"""


def _textOnPath(
    self: T,
    txt: str,
    fontsize: float,
    distance: float,
    cut: bool = True,
    combine: bool = False,
    clean: bool = True,
    font: str = "Arial",
    fontPath: Optional[str] = None,
    kind: Literal["regular", "bold", "italic"] = "regular",
    halign: Literal["center", "left", "right"] = "left",
    valign: Literal["center", "top", "bottom"] = "center",
    positionOnPath: float = 0.0,
) -> T:
    """
    Returns 3D text with the baseline following the given path.

    The parameters are largely the same as the
    `Workplane.text() <https://cadquery.readthedocs.io/en/latest/classreference.html#cadquery.Workplane.text>`_
    method. The **start** parameter (normally between 0.0 and 1.0) specify where on the path to
    start the text.

    The path that the text follows is defined by the last Edge or Wire in the
    Workplane stack. Path's defined outside of the Workplane can be used with the
    `add(<path>) <https://cadquery.readthedocs.io/en/latest/classreference.html#cadquery.Workplane.add>`_
    method.

    .. image:: textOnPath.png

    Args:
        txt: text to be rendered
        fontsize: size of the font in model units
        distance: the distance to extrude or cut, normal to the workplane plane, negative means opposite the normal direction
        cut: True to cut the resulting solid from the parent solids if found
        combine: True to combine the resulting solid with parent solids if found
        clean: call :py:meth:`clean` afterwards to have a clean shape
        font: font name
        fontPath: path to font file
        kind: font style
        halign: horizontal alignment
        valign: vertical alignment
        positionOnPath: the relative location on path to position the text, values must be between 0.0 and 1.0

    Returns:
        a CQ object with the resulting solid selected

    The returned object is always a Workplane object, and depends on whether combine is True, and
    whether a context solid is already defined:

    *  if combine is False, the new value is pushed onto the stack.
    *  if combine is true, the value is combined with the context solid if it exists,
       and the resulting solid becomes the new context solid.

    Examples::

        fox = (
            Workplane("XZ")
            .threePointArc((50, 30), (100, 0))
            .textOnPath(
                txt="The quick brown fox jumped over the lazy dog",
                fontsize=5,
                distance=1,
                start=0.1,
            )
        )

        clover = (
            Workplane("front")
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
    # The top edge or wire on the stack defines the path
    if not self.ctx.pendingWires and not self.ctx.pendingEdges:
        raise Exception("A pending edge or wire must be present to define the path")
    for stack_object in self.vals():
        if type(stack_object) == Edge:
            path = Wire.assembleEdges(self.ctx.pendingEdges)
            break
        if type(stack_object) == Wire:
            path = self.ctx.pendingWires.pop(0)
            break

    # The path was defined on an arbitrary plane, convert back to XY
    local_path = self.plane.toLocalCoords(path)
    result = Compound.make2DText(
        txt, fontsize, font, fontPath, kind, halign, valign, positionOnPath, local_path
    )
    if distance != 0:
        result = Compound.makeCompound(
            [Solid.extrudeLinear(f, Vector(0, 0, distance)) for f in result.Faces()]
        )
    # Reposition on this workplane
    result = result.transformShape(self.plane.rG)

    if cut:
        combine = "cut"

    return self._combineWithBase(result, combine, clean)


Workplane.textOnPath = _textOnPath


def _hexArray(
    self,
    diagonal: float,
    xCount: int,
    yCount: int,
    center: Union[bool, tuple[bool, bool]] = True,
):
    """Create Hex Array

    Creates a hexagon array of points and pushes them onto the stack.
    If you want to position the array at another point, create another workplane
    that is shifted to the position you would like to use as a reference

    Args:
        diagonal: tip to tip size of hexagon ( must be > 0)
        xCount: number of points ( > 0 )
        yCount: number of points ( > 0 )
        center: If True, the array will be centered around the workplane center.
            If False, the lower corner will be on the reference point and the array will
            extend in the positive x and y directions. Can also use a 2-tuple to specify
            centering along each axis.

    Returns:
        Places points on the Workplane stack
    """
    xSpacing = 3 * diagonal / 4
    ySpacing = diagonal * math.sqrt(3) / 2
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


Workplane.hexArray = _hexArray


def _workplane_thicken(self, depth: float, direction: "Vector" = None):
    """Thicken Face

    Find all of the faces on the stack and make them Solid objects by thickening
    along the normals.

    Args:
        depth: Amount to thicken face(s), can be positive or negative.
        direction: The direction vector can be used to
            indicate which way is 'up', potentially flipping the face normal direction
            such that many faces with different normals all go in the same direction
            (direction need only be +/- 90 degrees from the face normal). Defaults to None.

    Returns:
        A set of new objects on the Workplane stack
    """
    return self.newObject([f.thicken(depth, direction) for f in self.faces().vals()])


Workplane.thicken = _workplane_thicken


def _fastenerHole(
    self: T,
    hole_diameters: dict,
    fastener: Union["Nut", "Screw"],
    washers: list["Washer"],
    countersinkProfile: "Workplane",
    depth: Optional[float] = None,
    fit: Optional[Literal["Close", "Normal", "Loose"]] = None,
    material: Optional[Literal["Soft", "Hard"]] = None,
    counterSunk: Optional[bool] = True,
    captiveNut: Optional[bool] = False,
    baseAssembly: Optional["Assembly"] = None,
    hand: Optional[Literal["right", "left"]] = None,
    simple: Optional[bool] = False,
    clean: Optional[bool] = True,
) -> T:
    """Fastener Specific Hole

    Makes a counterbore clearance, tap or threaded hole for the given screw for each item
    on the stack. The surface of the hole is at the current workplane.

    Args:
        hole_diameters: either clearance or tap hole diameter specifications
        fastener: A nut or screw instance
        washers: A list of washer instances, can be empty
        countersinkProfile: the 2D side profile of the fastener (not including a screw's shaft)
        depth: hole depth. Defaults to through part.
        fit: one of "Close", "Normal", "Loose" which determines clearance hole diameter. Defaults to None.
        material: on of "Soft", "Hard" which determines tap hole size. Defaults to None.
        counterSunk: Is the fastener countersunk into the part?. Defaults to True.
        captiveNut: Countersink with a rectangular, filleted, hole. Defaults to False.
        baseAssembly: Assembly to add faster to. Defaults to None.
        hand: tap hole twist direction either "right" or "left". Defaults to None.
        simple: tap hole thread complexity selector. Defaults to False.
        clean: execute a clean operation remove extraneous internal features. Defaults to True.

    Raises:
        ValueError: fit or material not in hole_diameters dictionary

    Returns:
        the shape on the workplane stack with a new hole
    """
    from cq_warehouse.thread import IsoThread

    # If there is a thread direction, this is a threaded hole
    threaded_hole = not hand is None

    bore_direction = Vector(0, 0, -1)
    origin = Vector(0, 0, 0)

    # If no depth is given go through part, else align screw to bottom of hole
    if depth is None:
        hole_depth_offset = 0
        depth = self.largestDimension()
    elif isinstance(fastener, Screw):
        hole_depth_offset = fastener.length - depth
    else:
        hole_depth_offset = 0

    # Setscrews' countersink_profile is None so check if it exists
    # countersink_profile = fastener.countersink_profile(fit)
    countersink_profile = countersinkProfile
    if captiveNut:
        clearance = fastener.clearance_hole_diameters[fit] - fastener.thread_diameter
        head_offset = countersink_profile.vertices(">Z").val().Z
        if isinstance(fastener, (DomedCapNut, HexNut, UnchamferedHexagonNut)):
            fillet_radius = fastener.nut_diameter / 4
            rect_width = fastener.nut_diameter + clearance
            rect_height = fastener.nut_diameter * math.sin(math.pi / 3) + clearance
        elif isinstance(fastener, SquareNut):
            fillet_radius = fastener.nut_diameter / 8
            rect_height = fastener.nut_diameter * math.sqrt(2) / 2 + clearance
            rect_width = rect_height + 2 * fillet_radius + clearance

        countersink_cutter = (
            cq.Workplane("XY")
            .sketch()
            .rect(rect_width, rect_height)
            .vertices()
            .fillet(fillet_radius)
            .finalize()
            .extrude(-head_offset)
            .val()
        )
    elif counterSunk and not countersink_profile is None:
        head_offset = countersink_profile.vertices(">Z").val().Z
        countersink_cutter = (
            countersink_profile.revolve().translate((0, 0, -head_offset)).val()
        )
    else:
        head_offset = 0

    if threaded_hole:
        hole_radius = fastener.thread_diameter / 2
    else:
        key = fit if material is None else material
        try:
            hole_radius = hole_diameters[key] / 2
        except KeyError as e:
            raise ValueError(
                f"{key} invalid, must be one of {list(hole_diameters.keys())}"
            ) from e

    shank_hole = Solid.makeCylinder(
        radius=hole_radius,
        height=depth,
        pnt=origin,
        dir=bore_direction,
    )
    if counterSunk and not countersink_profile is None:
        fastener_hole = countersink_cutter.fuse(shank_hole)
    else:
        fastener_hole = shank_hole

    cskAngle = 82  # Common tip angle
    h = hole_radius / math.tan(math.radians(cskAngle / 2.0))
    drill_tip = Solid.makeCone(
        hole_radius, 0.0, h, bore_direction * depth, bore_direction
    )
    fastener_hole = fastener_hole.fuse(drill_tip)

    # Record the location of each hole for use in the assembly
    null_object = Solid.makeBox(1, 1, 1)
    relocated_test_objects = self.eachpoint(lambda loc: null_object.moved(loc), True)
    hole_locations = [loc.location() for loc in relocated_test_objects.vals()]

    # Add fasteners and washers to the base assembly if it was provided
    if baseAssembly is not None:
        for hole_loc in hole_locations:
            washer_thicknesses = 0
            if not washers is None:
                for washer in washers:
                    baseAssembly.add(
                        washer,
                        loc=hole_loc
                        * Location(
                            bore_direction
                            * (
                                head_offset
                                - fastener.length_offset()
                                - washer_thicknesses
                            )
                        ),
                    )
                    washer_thicknesses += washer.washer_thickness
                    # Create a metadata entry associating the auto-generated name & fastener
                    baseAssembly.metadata[baseAssembly.children[-1].name] = washer

            baseAssembly.add(
                fastener,
                loc=hole_loc
                * Location(
                    bore_direction
                    * (
                        head_offset
                        - fastener.length_offset()
                        - washer_thicknesses
                        - hole_depth_offset
                    )
                ),
            )
            # Create a metadata entry associating the auto-generated name & fastener
            baseAssembly.metadata[baseAssembly.children[-1].name] = fastener

    # Make holes in the stack solid object
    part = self.cutEach(lambda loc: fastener_hole.moved(loc), True, False)

    # Add threaded inserts
    if threaded_hole and not simple:
        thread = IsoThread(
            major_diameter=fastener.thread_diameter,
            pitch=fastener.thread_pitch,
            length=depth - head_offset,
            external=False,
            hand=hand,
        )
        for hole_loc in hole_locations:
            part = part.union(thread.moved(hole_loc * Location(bore_direction * depth)))
    if clean:
        part = part.clean()
    return part


Workplane.fastenerHole = _fastenerHole


def _clearanceHole(
    self: T,
    fastener: Union["Nut", "Screw"],
    washers: Optional[list["Washer"]] = None,
    fit: Optional[Literal["Close", "Normal", "Loose"]] = "Normal",
    depth: Optional[float] = None,
    counterSunk: Optional[bool] = True,
    captiveNut: Optional[bool] = False,
    baseAssembly: Optional["Assembly"] = None,
    clean: Optional[bool] = True,
) -> T:
    """Clearance Hole

    Put a clearance hole in a shape at the provided location

    For more information on how to use clearanceHole() see
    :ref:`Custom Holes <custom holes>`.

    Args:
        fastener: A nut or screw instance
        washers: A list of washer instances, can be empty
        fit: one of "Close", "Normal", "Loose" which determines clearance hole diameter. Defaults to "Normal".
        depth: hole depth. Defaults to through part.
        counterSunk: Is the fastener countersunk into the part?. Defaults to True.
        baseAssembly: Assembly to add faster to. Defaults to None.
        clean: execute a clean operation remove extraneous internal features. Defaults to True.

    Raises:
        ValueError: clearanceHole doesn't accept fasteners of type HeatSetNut - use insertHole instead

    Returns:
        the shape on the workplane stack with a new clearance hole
    """
    from cq_warehouse.fastener import HeatSetNut

    if isinstance(fastener, HeatSetNut):
        raise ValueError(
            "clearanceHole doesn't accept fasteners of type HeatSetNut - use insertHole instead"
        )

    if captiveNut and not isinstance(
        fastener, (DomedCapNut, HexNut, UnchamferedHexagonNut, SquareNut)
    ):
        raise ValueError(
            "Only DomedCapNut, HexNut, UnchamferedHexagonNut or SquareNut can be captive"
        )

    return self.fastenerHole(
        hole_diameters=fastener.clearance_hole_diameters,
        fastener=fastener,
        washers=washers,
        countersinkProfile=fastener.countersink_profile(fit),
        fit=fit,
        depth=depth,
        counterSunk=counterSunk,
        captiveNut=captiveNut,
        baseAssembly=baseAssembly,
        clean=clean,
    )


def _insertHole(
    self: T,
    fastener: "Nut",
    fit: Optional[Literal["Close", "Normal", "Loose"]] = "Normal",
    depth: Optional[float] = None,
    baseAssembly: Optional["Assembly"] = None,
    clean: Optional[bool] = True,
    manufacturingCompensation: float = 0.0,
) -> T:
    """Insert Hole

    Put a hole appropriate for an insert nut at the provided location

    For more information on how to use insertHole() see
    :ref:`Custom Holes <custom holes>`.

    Args:
        fastener: An insert nut instance
        fit: one of "Close", "Normal", "Loose" which determines clearance hole diameter. Defaults to "Normal".
        depth: hole depth. Defaults to through part.
        baseAssembly: Assembly to add faster to. Defaults to None.
        clean: execute a clean operation remove extraneous internal features. Defaults to True.
        manufacturingCompensation (float, optional): used to compensate for over-extrusion
            of 3D printers. A value of 0.2mm will reduce the radius of an external thread
            by 0.2mm (and increase the radius of an internal thread) such that the resulting
            3D printed part matches the target dimensions. Defaults to 0.0.

    Raises:
        ValueError: insertHole only accepts fasteners of type HeatSetNut

    Returns:
        the shape on the workplane stack with a new clearance hole
    """
    from cq_warehouse.fastener import HeatSetNut

    if not isinstance(fastener, HeatSetNut):
        raise ValueError("insertHole only accepts fasteners of type HeatSetNut")

    return self.fastenerHole(
        hole_diameters=fastener.clearance_hole_diameters,
        fastener=fastener,
        depth=depth,
        washers=[],
        countersinkProfile=fastener.countersink_profile(manufacturingCompensation),
        fit=fit,
        counterSunk=True,
        baseAssembly=baseAssembly,
        clean=clean,
    )


def _pressFitHole(
    self: T,
    bearing: "Bearing",
    interference: float = 0,
    fit: Optional[Literal["Close", "Normal", "Loose"]] = "Normal",
    depth: Optional[float] = None,
    baseAssembly: Optional["Assembly"] = None,
    clean: Optional[bool] = True,
) -> T:
    """Press Fit Hole

    Put a hole appropriate for a bearing at the provided location

    For more information on how to use pressFitHole() see
    :ref:`Custom Holes <custom holes>`.

    Args:
        bearing: A bearing instance
        interference: The amount the decrease the hole radius from the bearing outer radius. Defaults to 0.
        fit: one of "Close", "Normal", "Loose" which determines hole diameter for the bore. Defaults to "Normal".
        depth: hole depth. Defaults to through part.
        baseAssembly: Assembly to add faster to. Defaults to None.
        clean: execute a clean operation remove extraneous internal features. Defaults to True.

    Raises:
        ValueError: pressFitHole only accepts bearings of type Bearing

    Returns:
        the shape on the workplane stack with a new press fit hole
    """
    from cq_warehouse.bearing import Bearing

    if not isinstance(bearing, Bearing):
        raise ValueError("pressFitHole only accepts bearings")

    return self.fastenerHole(
        hole_diameters=bearing.clearance_hole_diameters,
        fastener=bearing,
        depth=depth,
        washers=[],
        countersinkProfile=bearing.countersink_profile(interference),
        fit=fit,
        counterSunk=True,
        baseAssembly=baseAssembly,
        clean=clean,
    )


def _tapHole(
    self: T,
    fastener: Union["Nut", "Screw"],
    washers: Optional[list["Washer"]] = None,
    material: Optional[Literal["Soft", "Hard"]] = "Soft",
    depth: Optional[float] = None,
    counterSunk: Optional[bool] = True,
    fit: Optional[Literal["Close", "Normal", "Loose"]] = "Normal",
    baseAssembly: Optional["Assembly"] = None,
    clean: Optional[bool] = True,
) -> T:
    """Tap Hole

    Put a tap hole in a shape at the provided location

    For more information on how to use tapHole() see
    :ref:`Custom Holes <custom holes>`.

    Args:
        fastener: A nut or screw instance
        washers: A list of washer instances, can be empty
        material: on of "Soft", "Hard" which determines tap hole size. Defaults to "Soft".
        depth: hole depth. Defaults to through part.
        counterSunk: Is the fastener countersunk into the part?. Defaults to True.
        fit: one of "Close", "Normal", "Loose" which determines clearance hole diameter. Defaults to None.
        baseAssembly: Assembly to add faster to. Defaults to None.
        clean: execute a clean operation remove extraneous internal features. Defaults to True.

    Raises:
        ValueError: tapHole doesn't accept fasteners of type HeatSetNut - use insertHole instead

    Returns:
        the shape on the workplane stack with a new tap hole
    """
    from cq_warehouse.fastener import HeatSetNut

    if isinstance(fastener, HeatSetNut):
        raise ValueError(
            "tapHole doesn't accept fasteners of type HeatSetNut - use insertHole instead"
        )

    return self.fastenerHole(
        hole_diameters=fastener.tap_hole_diameters,
        fastener=fastener,
        washers=washers,
        countersinkProfile=fastener.countersink_profile(fit),
        fit=fit,
        material=material,
        depth=depth,
        counterSunk=counterSunk,
        baseAssembly=baseAssembly,
        clean=clean,
    )


def _threadedHole(
    self: T,
    fastener: "Screw",
    depth: float,
    washers: Optional[list["Washer"]] = None,
    hand: Literal["right", "left"] = "right",
    simple: Optional[bool] = False,
    counterSunk: Optional[bool] = True,
    fit: Optional[Literal["Close", "Normal", "Loose"]] = "Normal",
    baseAssembly: Optional["Assembly"] = None,
    clean: Optional[bool] = True,
) -> T:
    """Threaded Hole

    Put a threaded hole in a shape at the provided location

    For more information on how to use threadedHole() see
    :ref:`Custom Holes <custom holes>`.

    Args:
        fastener: A nut or screw instance
        depth: hole depth. Defaults to through part.
        washers: A list of washer instances, can be empty
        hand: tap hole twist direction either "right" or "left". Defaults to None.
        simple (Optional[bool], optional): [description]. Defaults to False.
        counterSunk: Is the fastener countersunk into the part?. Defaults to True.
        fit: one of "Close", "Normal", "Loose" which determines clearance hole diameter. Defaults to None.
        baseAssembly: Assembly to add faster to. Defaults to None.
        clean: execute a clean operation remove extraneous internal features. Defaults to True.

    Raises:
        ValueError: threadedHole doesn't accept fasteners of type HeatSetNut - use insertHole instead

    Returns:
        the shape on the workplane stack with a new threaded hole
    """
    from cq_warehouse.fastener import HeatSetNut

    if isinstance(fastener, HeatSetNut):
        raise ValueError(
            "threadedHole doesn't accept fasteners of type HeatSetNut - use insertHole instead"
        )

    return self.fastenerHole(
        hole_diameters=fastener.clearance_hole_diameters,
        fastener=fastener,
        washers=washers,
        countersinkProfile=fastener.countersink_profile(fit),
        fit=fit,
        depth=depth,
        counterSunk=counterSunk,
        baseAssembly=baseAssembly,
        hand=hand,
        simple=simple,
        clean=clean,
    )


Workplane.clearanceHole = _clearanceHole
Workplane.insertHole = _insertHole
Workplane.pressFitHole = _pressFitHole
Workplane.tapHole = _tapHole
Workplane.threadedHole = _threadedHole


def _push_fastener_locations(
    self: T,
    fastener: Union["Nut", "Screw"],
    baseAssembly: "Assembly",
    offset: float = 0,
    flip: bool = False,
):
    """Push Fastener Locations

    Push the Location(s) of the given fastener relative to the given Assembly onto the workplane stack.

    Returns:
        Location objects on the workplane stack
    """

    # The locations need to be pushed as global not local object locations

    ns = self.__class__()
    ns.plane = Plane(origin=(0, 0, 0), xDir=(1, 0, 0), normal=(0, 0, 1))
    ns.parent = self
    locations = baseAssembly.fastenerLocations(fastener)
    ns.objects = [
        l * Location(Plane(origin=(0, 0, 0), normal=(0, 0, -1)), Vector(0, 0, offset))
        if flip
        else l * Location(Vector(0, 0, offset))
        for l in locations
    ]

    ns.ctx = self.ctx
    return ns


Workplane.pushFastenerLocations = _push_fastener_locations


def _makeFingerJoints_workplane(
    self: T,
    materialThickness: float,
    targetFingerWidth: float,
    kerfWidth: float = 0.0,
    baseAssembly: "Assembly" = None,
) -> T:
    """makeFingerJoints

    Starting with a base object and a set of selected edges, create Faces with
    finger joints that they could be laser cut from flat material.

    Example:

        For example, make a simple open topped laser cut box.

    .. code-block:: python

        finger_jointed_box_assembly = Assembly()
        finger_jointed_faces = (
            Workplane("XY")
            .box(100, 80, 60)
            .edges("not >Z")
            .makeFingerJoints(
                materialThickness=5,
                targetFingerWidth=10,
                kerfWidth=1,
                baseAssembly=finger_jointed_box_assembly,
            )
        )


    The assembly part is optional but if present the Assembly will
    contain the parts as if they were laser cut from a material of the
    given thickness.

    Args:
        self (T): workplane
        materialThickness (float): thickness of finger joints
        targetFingerWidth (float): approximate with of notch - actual finger width
            will be calculated such that there are an integer number of fingers on Edge
        kerfWidth (float, optional): Extra size to add (or subtract) to account
            for the kerf of the laser cutter. Defaults to 0.0.
        baseAssembly (Assembly, optional): Assembly to add parts to

    Raises:
        ValueError: Missing Solid object
        ValueError: Missing finger joint Edges

    Returns:
        T: Faces ready to be exported to DXF files and laser cut
    """
    solid_reference = self.findSolid(searchStack=True, searchParents=True)
    if not solid_reference:
        raise ValueError(
            "A solid object must be present to define the finger jointed faces"
        )

    finger_joint_edges = self.edges().vals()
    if not finger_joint_edges:
        raise ValueError(
            "An edge(s) must be present to defined the finger jointed edges"
        )

    logging.debug("Starting new finger jointed shape")

    jointed_faces = solid_reference.makeFingerJointFaces(
        finger_joint_edges, materialThickness, targetFingerWidth, kerfWidth
    )
    # If the assembly is requested, create Solids from faces and store them
    if baseAssembly:
        part_center = solid_reference.Center()
        for finger_jointed_face in jointed_faces:
            part = finger_jointed_face.thicken(
                materialThickness, part_center - finger_jointed_face.Center()
            )
            baseAssembly.add(
                part, color=Color(random.random(), random.random(), random.random())
            )
        logging.debug(f"{baseAssembly.doObjectsIntersect()=}")

    logging.debug("Completed finger jointed shape")

    return self.newObject(jointed_faces)


Workplane.makeFingerJoints = _makeFingerJoints_workplane


"""

Face extensions: thicken(), projectToShape(), embossToShape(), makeHoles(), makeFingerJoints(),
                 isInside()

"""


def _face_thicken(self, depth: float, direction: "Vector" = None) -> "Solid":
    """Thicken Face

    Create a solid from a potentially non planar face by thickening along the normals.

    .. image:: thickenFace.png

    Non-planar faces are thickened both towards and away from the center of the sphere.

    Args:
        depth: Amount to thicken face(s), can be positive or negative.
        direction: The direction vector can be used to
            indicate which way is 'up', potentially flipping the face normal direction
            such that many faces with different normals all go in the same direction
            (direction need only be +/- 90 degrees from the face normal). Defaults to None.

    Raises:
        RuntimeError: Opencascade internal failures

    Returns:
        The resulting Solid object
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
        result = Solid(solid.Shape())
    except StdFail_NotDone as e:
        raise RuntimeError("Error applying thicken to given Face") from e

    return result.clean()


Face.thicken = _face_thicken


def _face_projectToShape(
    self,
    targetObject: "Shape",
    direction: "VectorLike" = None,
    center: "VectorLike" = None,
    internalFacePoints: list["Vector"] = [],
) -> list["Face"]:
    """Project Face to target Object

    Project a Face onto a Shape generating new Face(s) on the surfaces of the object
    one and only one of `direction` or `center` must be provided.

    The two types of projections are illustrated below:

    .. image:: flatProjection.png
        :alt: flatProjection

    .. image:: conicalProjection.png
        :alt: conicalProjection

    Note that an array of Faces is returned as the projection might result in faces
    on the "front" and "back" of the object (or even more if there are intermediate
    surfaces in the projection path). Faces "behind" the projection are not
    returned.

    To help refine the resulting face, a list of planar points can be passed to
    augment the surface definition. For example, when projecting a circle onto a
    sphere, a circle will result which will get converted to a planar circle face.
    If no points are provided, a single center point will be generated and used for
    this purpose.

    Args:
        targetObject: Object to project onto
        direction: Parallel projection direction. Defaults to None.
        center: Conical center of projection. Defaults to None.
        internalFacePoints: Points refining shape. Defaults to [].

    Raises:
        ValueError: Only one of direction or center must be provided

    Returns:
        Face(s) projected on target object
    """

    # There are four phase to creation of the projected face:
    # 1- extract the outer wire and project
    # 2- extract the inner wires and project
    # 3- extract surface points within the outer wire
    # 4- build a non planar face

    if not (direction is None) ^ (center is None):
        raise ValueError("One of either direction or center must be provided")
    if direction is not None:
        direction_vector = Vector(direction)
        center_point = None
    else:
        direction_vector = None
        center_point = Vector(center)

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
        else Wire(w.wrapped.Reversed())
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
            planar_grid = Edge.makeLine(
                planar_outer_wire.positionAt(0), internalFacePoints[0]
            )
        else:
            planar_grid = Wire.makePolygon([Vector(v) for v in internalFacePoints])
        projected_grids = planar_grid.projectToShape(
            targetObject, direction_vector, center_point
        )
        projected_grid_points = [
            [Vector(*v.toTuple()) for v in grid.Vertices()] for grid in projected_grids
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


Face.projectToShape = _face_projectToShape


def _face_embossToShape(
    self,
    targetObject: "Shape",
    surfacePoint: "VectorLike",
    surfaceXDirection: "VectorLike",
    internalFacePoints: list["Vector"] = None,
    tolerance: float = 0.01,
) -> "Face":
    """Emboss Face on target object

    Emboss a Face on the XY plane onto a Shape while maintaining
    original face dimensions where possible.

    Unlike projection, a single Face is returned. The internalFacePoints
    parameter works as with projection.

    Args:
        targetObject: Object to emboss onto
        surfacePoint: Point on target object to start embossing
        surfaceXDirection: Direction of X-Axis on target object
        internalFacePoints: Surface refinement points. Defaults to None.
        tolerance: maximum allowed error in embossed wire length. Defaults to 0.01.

    Returns:
        Face: Embossed face
    """
    # There are four phase to creation of the projected face:
    # 1- extract the outer wire and project
    # 2- extract the inner wires and project
    # 3- extract surface points within the outer wire
    # 4- build a non planar face

    # Phase 1 - outer wire
    planar_outer_wire = self.outerWire()
    planar_outer_wire_orientation = planar_outer_wire.wrapped.Orientation()
    embossed_outer_wire = planar_outer_wire.embossToShape(
        targetObject, surfacePoint, surfaceXDirection, tolerance
    )

    # Phase 2 - inner wires
    planar_inner_wires = [
        w
        if w.wrapped.Orientation() != planar_outer_wire_orientation
        else Wire(w.wrapped.Reversed())
        for w in self.innerWires()
    ]
    embossed_inner_wires = [
        w.embossToShape(targetObject, surfacePoint, surfaceXDirection, tolerance)
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
            planar_grid = Edge.makeLine(
                planar_outer_wire.positionAt(0), internalFacePoints[0]
            )
        else:
            planar_grid = Wire.makePolygon([Vector(v) for v in internalFacePoints])

        embossed_grid = planar_grid.embossToShape(
            targetObject, surfacePoint, surfaceXDirection, tolerance
        )
        embossed_surface_points = [
            Vector(*v.toTuple()) for v in embossed_grid.Vertices()
        ]

    # Phase 4 - Build the faces
    embossed_face = embossed_outer_wire.makeNonPlanarFace(
        surfacePoints=embossed_surface_points, interiorWires=embossed_inner_wires
    )

    return embossed_face


Face.embossToShape = _face_embossToShape


def _face_makeHoles(self, interiorWires: list["Wire"]) -> "Face":
    """Make Holes in Face

    Create holes in the Face 'self' from interiorWires which must be entirely interior.
    Note that making holes in Faces is more efficient than using boolean operations
    with solid object. Also note that OCCT core may fail unless the orientation of the wire
    is correct - use ``cq.Wire(forward_wire.wrapped.Reversed())`` to reverse a wire.

    Example:

        For example, make a series of slots on the curved walls of a cylinder.

    .. code-block:: python

        cylinder = cq.Workplane("XY").cylinder(100, 50, centered=(True, True, False))
        cylinder_wall = cylinder.faces("not %Plane").val()
        path = cylinder.section(50).edges().val()
        slot_wire = cq.Workplane("XY").slot2D(60, 10, angle=90).wires().val()
        embossed_slot_wire = slot_wire.embossToShape(
            targetObject=cylinder.val(),
            surfacePoint=path.positionAt(0),
            surfaceXDirection=path.tangentAt(0),
        )
        embossed_slot_wires = [
            embossed_slot_wire.rotate((0, 0, 0), (0, 0, 1), a) for a in range(90, 271, 20)
        ]
        cylinder_wall_with_holes = cylinder_wall.makeHoles(embossed_slot_wires)

    .. image:: slotted_cylinder.png

    Args:
        interiorWires: a list of hole outline wires

    Raises:
        RuntimeError: adding interior hole in non-planar face with provided interiorWires
        RuntimeError: resulting face is not valid

    Returns:
        Face: 'self' with holes
    """
    # Add wires that define interior holes - note these wires must be entirely interior
    makeface_object = BRepBuilderAPI_MakeFace(self.wrapped)
    for w in interiorWires:
        makeface_object.Add(w.wrapped)
    try:
        surface_face = Face(makeface_object.Face())
    except StdFail_NotDone as e:
        raise RuntimeError(
            "Error adding interior hole in non-planar face with provided interiorWires"
        ) from e

    surface_face = surface_face.fix()
    # if not surface_face.isValid():
    #     raise RuntimeError("non planar face is invalid")

    return surface_face


Face.makeHoles = _face_makeHoles


def _isInside_face(self, point: VectorLike, tolerance: float = 1.0e-6) -> bool:
    """Point inside Face

    Returns whether or not the point is inside a Face within the specified tolerance.
    Points on the edge of the Face are considered inside.

    Args:
        point (VectorLike): tuple or Vector representing 3D point to be tested
        tolerance (float, optional): tolerance for inside determination. Defaults to 1.0e-6.

    Returns:
        bool: indicating whether or not point is within Face
    """
    return Compound.makeCompound([self]).isInside(point, tolerance)


Face.isInside = _isInside_face


def _makeFingerJoints_face(
    self: "Face",
    fingerJointEdge: "Edge",
    fingerDepth: float,
    targetFingerWidth: float,
    cornerFaceCounter: dict,
    openInternalVertices: dict,
    alignToBottom: bool = True,
    externalCorner: bool = True,
    faceIndex: int = 0,
) -> "Face":
    """makeFingerJoints

    Given a Face and an Edge, create finger joints by cutting notches.

    Args:
        self (Face): Face to modify
        fingerJointEdge (Edge): Edge of Face to modify
        fingerDepth (float): thickness of the notch from edge
        targetFingerWidth (float): approximate with of notch - actual finger width
            will be calculated such that there are an integer number of fingers on Edge
        cornerFaceCounter (dict): the set of faces associated with every corner
        openInternalVertices (dict): is a vertex part an opening?
        alignToBottom (bool, optional): start with a finger or notch. Defaults to True.
        externalCorner (bool, optional): cut from external corners, add to internal corners.
            Defaults to True.
        faceIndex (int, optional): the index of the current face. Defaults to 0.

    Returns:
        Face: the Face with notches on one edge
    """
    edge_length = fingerJointEdge.Length()
    finger_count = round(edge_length / targetFingerWidth)
    finger_width = edge_length / (finger_count)
    face_center = self.Center()

    edge_origin = fingerJointEdge.positionAt(0)
    edge_tangent = fingerJointEdge.tangentAt(0)
    edge_plane = Plane(
        origin=edge_origin,
        xDir=edge_tangent,
        normal=edge_tangent.cross((face_center - edge_origin).normalized()),
    )
    # Need to determine the vertex that corresponds to the positionAt(0) point
    end_vertex_index = int(edge_origin == fingerJointEdge.Vertices()[0].toVector())
    start_vertex_index = (end_vertex_index + 1) % 2
    start_vertex = fingerJointEdge.Vertices()[start_vertex_index]
    end_vertex = fingerJointEdge.Vertices()[end_vertex_index]
    if start_vertex.toVector() != edge_origin:
        raise RuntimeError("Error in determining start_vertex")

    if alignToBottom and finger_count % 2 == 0:
        finger_offset = -finger_width / 2
        tab_count = finger_count // 2
    elif alignToBottom and finger_count % 2 == 1:
        finger_offset = 0
        tab_count = (finger_count + 1) // 2
    elif not alignToBottom and finger_count % 2 == 0:
        finger_offset = +finger_width / 2
        tab_count = finger_count // 2
    elif not alignToBottom and finger_count % 2 == 1:
        finger_offset = 0
        tab_count = finger_count // 2

    # Calculate the positions of the cutouts (for external corners) or extra tabs
    # (for internal corners)
    x_offset = (tab_count - 1) * finger_width - edge_length / 2 + finger_offset
    finger_positions = [
        Vector(i * 2 * finger_width - x_offset, 0, 0) for i in range(tab_count)
    ]

    # Align the Face to the given Edge
    face_local = edge_plane.toLocalCoords(self)

    # Note that Face.makePlane doesn't work here as a rectangle creator
    # as it is inconsistent as to what is the x direction.
    finger = cq.Face.makeFromWires(
        cq.Wire.makeRect(
            finger_width,
            2 * fingerDepth,
            center=cq.Vector(),
            xDir=cq.Vector(1, 0, 0),
            normal=face_local.normalAt(Vector()) * -1,
        ),
        [],
    )
    start_part_finger = cq.Face.makeFromWires(
        cq.Wire.makeRect(
            finger_width - fingerDepth,
            2 * fingerDepth,
            center=cq.Vector(fingerDepth / 2, 0, 0),
            xDir=cq.Vector(1, 0, 0),
            normal=face_local.normalAt(Vector()) * -1,
        ),
        [],
    )
    end_part_finger = start_part_finger.translate((-fingerDepth, 0, 0))

    # Logging strings
    tab_type = {finger: "whole", start_part_finger: "start", end_part_finger: "end"}
    vertex_type = {True: "start", False: "end"}

    def lenCornerFaceCounter(corner: Vertex) -> int:
        return len(cornerFaceCounter[corner]) if corner in cornerFaceCounter else 0

    for position in finger_positions:
        # Is this a corner?, if so which one
        if position.x == finger_width / 2:
            corner = start_vertex
            part_finger = start_part_finger
        elif position.x == edge_length - finger_width / 2:
            corner = end_vertex
            part_finger = end_part_finger
        else:
            corner = None

        cq.Face.operation = cq.Face.cut if externalCorner else cq.Face.fuse

        if corner is not None:
            # To avoid missing corners (or extra inside corners) check to see if
            # the corner is already notched
            if (
                face_local.isInside(position)
                and externalCorner
                or not face_local.isInside(position)
                and not externalCorner
            ):
                if corner in cornerFaceCounter:
                    cornerFaceCounter[corner].add(faceIndex)
                else:
                    cornerFaceCounter[corner] = set([faceIndex])
            if externalCorner:
                tab = finger if lenCornerFaceCounter(corner) < 3 else part_finger
            else:
                # tab = part_finger if lenCornerFaceCounter(corner) < 3 else finger
                if corner in openInternalVertices:
                    tab = finger
                else:
                    tab = part_finger if lenCornerFaceCounter(corner) < 3 else finger

            # Modify the face
            face_local = face_local.operation(tab.translate(position))

            logging.debug(
                f"Corner {corner}, vertex={vertex_type[corner==start_vertex]}, "
                f"{lenCornerFaceCounter(corner)=}, normal={self.normalAt(face_center)}, tab={tab_type[tab]}, "
                f"{face_local.intersect(tab.translate(position)).Area()=:.0f}, {tab.Area()/2=:.0f}"
            )
        else:
            face_local = face_local.operation(finger.translate(position))

        # Need to clean and revert the generated Compound back to a Face
        face_local = face_local.clean().Faces()[0]

    # Relocate the face back to its original position
    new_face = edge_plane.fromLocalCoords(face_local)

    return new_face


Face.makeFingerJoints = _makeFingerJoints_face

"""

Compound extensions: make2DText

"""


def _make2DText_compound(
    cls,
    txt: str,
    fontsize: float,
    font: str = "Arial",
    fontPath: Optional[str] = None,
    fontStyle: Literal["regular", "bold", "italic"] = "regular",
    halign: Literal["center", "left", "right"] = "left",
    valign: Literal["center", "top", "bottom"] = "center",
    positionOnPath: float = 0.0,
    textPath: Union["Edge", "Wire"] = None,
) -> "Compound":
    """
    2D Text that optionally follows a path.

    The text that is created can be combined as with other sketch features by specifying
    a mode or rotated by the given angle.  In addition, edges have been previously created
    with arc or segment, the text will follow the path defined by these edges. The start
    parameter can be used to shift the text along the path to achieve precise positioning.

    Args:
        txt: text to be rendered
        fontsize: size of the font in model units
        font: font name
        fontPath: path to font file
        fontStyle: one of ["regular", "bold", "italic"]. Defaults to "regular".
        halign: horizontal alignment, one of ["center", "left", "right"].
            Defaults to "left".
        valign: vertical alignment, one of ["center", "top", "bottom"].
            Defaults to "center".
        positionOnPath: the relative location on path to position the text, between 0.0 and 1.0.
            Defaults to 0.0.
        textPath: a path for the text to follows. Defaults to None - linear text.

    Returns:
        a Compound object containing multiple Faces representing the text

    Examples::

        fox = cq.Compound.make2DText(
            txt="The quick brown fox jumped over the lazy dog",
            fontsize=10,
            positionOnPath=0.1,
            textPath=jump_edge,
        )

    """

    def position_face(orig_face: "Face") -> "Face":
        """
        Reposition a face to the provided path

        Local coordinates are used to calculate the position of the face
        relative to the path. Global coordinates to position the face.
        """
        bbox = orig_face.BoundingBox()
        face_bottom_center = Vector((bbox.xmin + bbox.xmax) / 2, 0, 0)
        relative_position_on_wire = positionOnPath + face_bottom_center.x / path_length
        wire_tangent = textPath.tangentAt(relative_position_on_wire)
        wire_angle = -180 * Vector(1, 0, 0).getSignedAngle(wire_tangent) / math.pi
        wire_position = textPath.positionAt(relative_position_on_wire)

        return orig_face.translate(wire_position - face_bottom_center).rotate(
            wire_position,
            wire_position + Vector(0, 0, 1),
            wire_angle,
        )

    font_kind = {
        "regular": Font_FA_Regular,
        "bold": Font_FA_Bold,
        "italic": Font_FA_Italic,
    }[fontStyle]

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
        float(fontsize),
    )
    text_flat = Compound(builder.Perform(font_i, NCollection_Utf8String(txt)))

    bb = text_flat.BoundingBox()

    t = Vector()

    if halign == "center":
        t.x = -bb.xlen / 2
    elif halign == "right":
        t.x = -bb.xlen

    if valign == "center":
        t.y = -bb.ylen / 2
    elif valign == "top":
        t.y = -bb.ylen

    text_flat = text_flat.translate(t)

    if textPath is not None:
        path_length = textPath.Length()
        text_flat = Compound.makeCompound([position_face(f) for f in text_flat.Faces()])

    return text_flat


# Monkey patch a class method
Compound.make2DText = MethodType(_make2DText_compound, Compound)

"""

Sketch extensions: text(), val(), vals(), add(), mirror_x(), mirror_y(), spline(),
                   polyline(), center_arc(), tangent_arc(), three_point_arc(), bounding_box(),
                   push_points()

"""


class Mode(Enum):
    """Combination Mode"""

    ADDITION = auto()
    SUBTRACTION = auto()
    INTERSECTION = auto()
    CONSTRUCTION = auto()


def _snap_to_vector_sketch(
    self,
    pts: Iterable[Union[Point, str]],
    find_tangents: bool = False,
) -> list[Vector]:
    """Snap to Vector

    Convert Snaps to Vector

    Args:
        pts (Union[Point,str]): list of Snaps
        find_tangents (bool): return tangents instead of positions. Defaults to False.

    Returns:
        list(Vector): a list of Vectors possibly extracted from tagged objects
    """
    positions = {"start": 0.0, "middle": 0.5, "end": 1.0}
    snap_pts = []

    for p in pts:
        if isinstance(p, str):
            snap_parts = p.split("@")
            try:
                position = float(snap_parts[1])
            except ValueError:
                try:
                    position = positions[snap_parts[1]]
                except KeyError:
                    raise ValueError(
                        "snap position must be a float or one of 'start', 'middle', 'end'"
                    )
            for edge_or_wire in self._tags[snap_parts[0]]:
                if find_tangents:
                    snap_pts.append(edge_or_wire.tangentAt(position))
                else:
                    snap_pts.append(edge_or_wire.positionAt(position))

        elif isinstance(p, tuple):
            snap_pts.append(Vector(p))
        else:
            snap_pts.append(p)

    return snap_pts


Sketch.snap_to_vector = _snap_to_vector_sketch


class Mode(Enum):
    """Combination Mode"""

    ADDITION = auto()
    SUBTRACTION = auto()
    INTERSECTION = auto()
    CONSTRUCTION = auto()
    PRIVATE = auto()


class Font_Style(Enum):
    """Text Font Styles"""

    REGULAR = auto()
    BOLD = auto()
    ITALIC = auto()


class Halign(Enum):
    """Horizontal Alignment"""

    CENTER = auto()
    LEFT = auto()
    RIGHT = auto()


class Valign(Enum):
    """Vertical Alignment"""

    CENTER = auto()
    TOP = auto()
    BOTTOM = auto()


def _text_sketch(
    self: T,
    txt: str,
    fontsize: float,
    font: str = "Arial",
    font_path: Optional[str] = None,
    font_style: Literal["regular", "bold", "italic"] = "regular",
    halign: Literal["center", "left", "right"] = "left",
    valign: Literal["center", "top", "bottom"] = "center",
    # font_style: Font_Style = Font_Style.REGULAR,
    # halign: Halign = Halign.LEFT,
    # valign: Valign = Valign.CENTER,
    position_on_path: float = 0.0,
    angle: float = 0,
    mode: "Modes" = "a",
    # mode: Mode = Mode.ADDITION,
    tag: Optional[str] = None,
) -> T:
    """
    Text that optionally follows a path.

    The text that is created can be combined as with other sketch features by specifying
    a mode or rotated by the given angle.  In addition, the text will follow the path defined
    by edges that have been previously created with arc or segment. The positionOnPath
    parameter can be used to shift the text along the path to achieve precise positioning.

    Examples::

        simple_text = cq.Sketch().text("simple", 10, angle=10)

        loop_sketch = (
            cq.Sketch()
                .arc((-50, 0), 50, 90, 270)
                .arc((50, 0), 50, 270, 270)
                .text("loop_" * 20, 10)
        )

    Args:
        txt: text to be rendered
        fontsize: size of the font in model units
        font: font name
        font_path: system path to font file
        font_style: one of ["regular", "bold", "italic"]. Defaults to "regular".
        halign: horizontal alignment, one of ["center", "left", "right"].
            Defaults to "left".
        valign: vertical alignment, one of ["center", "top", "bottom"].
            Defaults to "center".
        position_on_path: the relative location on path to locate the text, between 0.0 and 1.0.
            Defaults to 0.0.
        angle: rotation angle. Defaults to 0.0.
        mode: combination mode, one of ["a","s","i","c"]. Defaults to "a".
        tag: feature label. Defaults to None.

    Returns:
        a Sketch object

    """
    if self._edges:
        text_path = Wire.assembleEdges(self._edges)
    else:
        text_path = None

    res = Compound.make2DText(
        txt,
        fontsize,
        font,
        font_path,
        font_style,
        halign,
        valign,
        # font_style.name.lower(),
        # halign.name.lower(),
        # valign.name.lower(),
        position_on_path,
        text_path,
    )
    orientation = Location(Vector(), Vector(0, 0, 1), angle)
    return self.each(lambda l: res.located(l * orientation), mode, tag)


Sketch.text = _text_sketch


def _vals_sketch(self) -> list[Union["Vertex", "Wire", "Edge", "Face"]]:
    """Return a list of selected values

    Examples::

        face_objects = cq.Sketch().text("test", 10).faces().vals()

    Raises:
        ValueError: Nothing selected

    Returns:
        list[Union[Vertex, Wire, Edge, Face]]: List of selected occ_impl objects

    """
    if not self._selection:
        raise ValueError("Nothing selected")
    return self._selection


Sketch.vals = _vals_sketch


def _val_sketch(self) -> Union["Vertex", "Wire", "Edge", "Face"]:
    """Return the first selected value

    Examples::

        edge_object = cq.Sketch().arc((-50, 0), 50, 90, 270).edges().val()

    Raises:
        ValueError: Nothing selected

    Returns:
        Union[Vertex, Wire, Edge, Face]: The first selected occ_impl object

    """
    if not self._selection:
        raise ValueError("Nothing selected")
    return self._selection[0]


Sketch.val = _val_sketch


def _add_sketch(
    self: T,
    obj: Union["Wire", "Edge", "Face"],
    angle: float = 0,
    mode: "Modes" = "a",
    # mode: Mode = Mode.ADDITION,
    tag: Optional[str] = None,
) -> T:
    """add

    Add a Wire, Edge or Face to this sketch

    Examples::

        added_edge = cq.Sketch().arc((50, 0), 50, 270, 270).add(external_edge).assemble()

    Args:
        obj (Union[Wire, Edge, Face]): the object to add
        angle (float, optional): rotation angle. Defaults to 0.0.
        mode (Modes, optional): combination mode, one of ["a","s","i","c"]. Defaults to "a".
        tag (Optional[str], optional): feature label. Defaults to None.

    Returns:
        Updated sketch

    """
    if isinstance(obj, Edge):
        self.edge(obj.rotate(Vector(), Vector(0, 0, 1), angle), tag, mode == "c")
        # self.edge(
        #     obj.rotate(Vector(), Vector(0, 0, 1), angle), tag, mode == Mode.CONSTRUCTION
        # )
    elif isinstance(obj, Wire):
        # obj.forConstruction = mode == "c"
        obj.forConstruction = mode == Mode.CONSTRUCTION
        self._wires.append(obj.rotate(Vector(), Vector(0, 0, 1), angle))
        if tag:
            self._tag([obj], tag)
    elif isinstance(obj, Face):
        self.each(
            lambda l: obj.rotate(Vector(), Vector(0, 0, 1), angle).located(l),
            mode,
            # mode.name.lower()[0:1],
            tag,
        )

    return self


Sketch.add = _add_sketch


def _mirror_x_sketch(self):
    """Mirror across X axis

    Mirror the selected items across the X axis

    Raises:
        ValueError: Nothing selected

    Returns:
        Updated Sketch
    """
    if not self._selection:
        raise ValueError("Nothing selected")

    mirrored_selections = Plane.named("XY").mirrorInPlane(self._selection, axis="X")
    for mirrored_obj in mirrored_selections:
        self.add(mirrored_obj)
    return self


Sketch.mirror_x = _mirror_x_sketch


def _mirror_y_sketch(self):
    """Mirror across Y axis

    Mirror the selected items across the Y axis

    Raises:
        ValueError: Nothing selected

    Returns:
        Updated Sketch
    """
    if not self._selection:
        raise ValueError("Nothing selected")

    mirrored_selections = Plane.named("XY").mirrorInPlane(self._selection, axis="Y")
    for mirrored_obj in mirrored_selections:
        self.add(mirrored_obj)
    return self


Sketch.mirror_y = _mirror_y_sketch


def _spline_sketch(
    self: T,
    *pts: Union[Point, str],
    tangents: Iterable[Union[Point, str]] = None,
    tangent_scalars: Iterable[float] = None,
    periodic: bool = False,
    # mode: Mode = Mode.ADDITION,
    tag: str = None,
    for_construction: bool = False,
) -> T:
    """spline

    Construct a spline

    Examples::

        boomerang = (
            cq.Sketch()
            .center_arc(center=(0, 0), radius=10, start_angle=0, arc_size=90, tag="c")
            .spline("c@1", (10, 10), "c@0", tangents=("c@1", "c@0"))
        )

    Args:
        pts (Union[Point,str]): sequence of points or snaps defining the spline
        tangents (Iterable[Union[Point, str]], optional): spline tangents or snaps. Defaults to None.
        tangent_scalars (Iterable[float], optional): tangent multipliers to refine the shape.
            Defaults to None.
        periodic (bool, optional): creation of periodic curves. Defaults to False.
        tag (str, optional): feature label. Defaults to None.
        for_construction (bool, optional): edge used to build other geometry. Defaults to False.

    Returns:
        Updated Sketch
    """

    spline_pts = self.snap_to_vector(pts)
    if tangents:
        spline_tangents = self.snap_to_vector(tangents, find_tangents=True)
    else:
        spline_tangents = None

    if tangents and not tangent_scalars:
        scalars = [1.0] * len(tangents)
    else:
        scalars = tangent_scalars

    spline = Edge.makeSpline(
        [p if isinstance(p, Vector) else Vector(*p) for p in spline_pts],
        tangents=[
            t * s if isinstance(t, Vector) else Vector(*t) * s
            for t, s in zip(spline_tangents, scalars)
        ]
        if spline_tangents
        else None,
        periodic=periodic,
        scale=tangent_scalars is None,
    )

    return self.edge(spline, tag, for_construction)
    # return self.edge(spline, tag, mode == Mode.CONSTRUCTION)


Sketch.spline = _spline_sketch


def _polyline_sketch(
    self,
    *pts: Union[Point, str],
    # mode: Mode = Mode.ADDITION,
    tag: str = None,
    for_construction: bool = False,
):
    """Polyline

    A polyline defined by two or more points or snaps

    Examples::

        pline = cq.Sketch().polyline((0, 0), (1, 1), (2, 0), (3, 1), (4, 0))

        triangle = (
            cq.Sketch()
            .polyline((0, 0), (2, 0), tag="base")
            .polyline("base@0", (1, 1), tag="left")
            .polyline("left@1", "base@1")
        )

    Args:
        pts (Union[Point,str]): sequence of points or snaps
        tag (str, optional): feature label. Defaults to None.
        for_construction (bool, optional): edge used to build other geometry. Defaults to False.

    Raises:
        ValueError: polyline requires two or more pts

    Returns:
        Updated sketch
    """
    if len(pts) < 2:
        raise ValueError("polyline requires two or more pts")

    lines_pts = self.snap_to_vector(pts)

    new_edges = [
        Edge.makeLine(lines_pts[i], lines_pts[i + 1]) for i in range(len(lines_pts) - 1)
    ]

    for e in new_edges:
        e.forConstruction = for_construction
    self._edges.extend(new_edges)

    if tag:
        # self._tag([new_line], tag)
        self._tag(new_edges, tag)

    return self


Sketch.polyline = _polyline_sketch


def _center_arc_sketch(
    self,
    center: Union[Point, str],
    radius: float,
    start_angle: float,
    arc_size: float,
    # mode: Mode = Mode.ADDITION,
    tag: str = None,
    for_construction: bool = False,
):
    """Center Arc

    A partial or complete circle with defined center

    Examples::

        chord = (
            cq.Sketch()
            .center_arc(center=(0, 0), radius=10, start_angle=0, arc_size=60, tag="c")
            .polyline("c@1", "c@0")
            .assemble()
        )

    Args:
        center (Union[Point, str]): point or snap defining the arc center
        radius (float): arc radius
        start_angle (float): in degrees, where zero corresponds to the +vs X axis
        arc_size (float): size of arc counter clockwise from start
        tag (str, optional): feature label. Defaults to None.
        for_construction (bool, optional): edge used to build other geometry. Defaults to False.

    Returns:
        Updated sketch
    """
    centers = self.snap_to_vector([center])

    if abs(arc_size) >= 360:
        arc = Edge.makeCircle(
            radius,
            centers[0],
            angle1=start_angle,
            angle2=start_angle,
            orientation=arc_size > 0,
        )
    else:
        p0 = centers[0]
        p1 = p0 + radius * Vector(
            math.cos(math.radians(start_angle)), math.sin(math.radians(start_angle))
        )
        p2 = p0 + radius * Vector(
            math.cos(math.radians(start_angle + arc_size / 2)),
            math.sin(math.radians(start_angle + arc_size / 2)),
        )
        p3 = p0 + radius * Vector(
            math.cos(math.radians(start_angle + arc_size)),
            math.sin(math.radians(start_angle + arc_size)),
        )
        arc = Edge.makeThreePointArc(p1, p2, p3)

    return self.edge(arc, tag, for_construction)
    # return self.edge(arc, tag, mode == Mode.CONSTRUCTION)


Sketch.center_arc = _center_arc_sketch


def _three_point_arc_sketch(
    self: T,
    *pts: Union[Point, str],
    # mode: Mode = Mode.ADDITION,
    tag: str = None,
    for_construction: bool = False,
) -> T:
    """Three Point Arc

    Construct an arc through a sequence of points or snaps

    Examples::

        three_point_arc = (
            cq.Sketch()
            .polyline((0, 10), (0, 0), (10, 0), tag="p")
            .three_point_arc("p@0", "p@0.5", "p@1")
        )

    Args:
        pts (Union[Point,str]): sequence of points or snaps
        tag (str, optional): feature label. Defaults to None.
        for_construction (bool, optional): edge used to build other geometry. Defaults to False.

    Raises:
        ValueError: three_point_arc requires three points

    Returns:
        Updated sketch

    """
    arc_pts = self.snap_to_vector(pts)
    if len(arc_pts) != 3:
        raise ValueError("three_point_arc requires three points")

    arc = Edge.makeThreePointArc(arc_pts[0], arc_pts[1], arc_pts[2])

    return self.edge(arc, tag, for_construction)
    # return self.edge(arc, tag, mode == Mode.CONSTRUCTION)


Sketch.three_point_arc = _three_point_arc_sketch


def _tangent_arc_sketch(
    self,
    *pts: Union[Point, str],
    tangent: Point = None,
    tangent_from_first: bool = True,
    # mode: Mode = Mode.ADDITION,
    tag: Optional[str] = None,
    for_construction: bool = False,
):
    """Tangent Arc

    Create an arc defined by the provided points and a tangent

    Examples::

        tangent_arc = (
            cq.Sketch()
            .center_arc(center=(0, 0), radius=10, start_angle=0, arc_size=90, tag="c")
            .tangent_arc("c@0.5", (10, 10), tag="t")
        )

    Args:
        pts (Union[Point,str]): start and end point or snap of arc
        tangent (Point, optional): tangent value if snaps aren't used. Defaults to None.
        tangent_from_first (bool, optional) point to align tangent to. Note that
            using a value of False will build the arc in the reverse direction. Defaults to True.
        tag (str, optional): feature label. Defaults to None.
        for_construction (bool, optional): edge used to build other geometry. Defaults to False.

    Raises:
        ValueError: tangentArc requires two points
        ValueError: no tangent provided

    Returns:
        Updated sketch
    """
    arc_pts = self.snap_to_vector(pts)
    if len(arc_pts) != 2:
        raise ValueError("tangent_arc requires two points")

    if not isinstance(pts[not tangent_from_first], str) and not tangent:
        raise ValueError(
            "tangent_arc requires a edge that determines the tangent or an explicit tangent"
        )
    if tangent is None:
        arc_tangents = self.snap_to_vector(pts, find_tangents=True)
    else:
        arc_tangents = [Vector(tangent)]

    arc = Edge.makeTangentArc(
        arc_pts[not tangent_from_first], arc_tangents[0], arc_pts[tangent_from_first]
    )

    return self.edge(arc, tag, for_construction)
    # return self.edge(arc, tag, mode == Mode.CONSTRUCTION)


Sketch.tangent_arc = _tangent_arc_sketch


def _push_points_sketch(
    self: T,
    *pts: Union[Union[Point, str], Location],
    tag: Optional[str] = None,
) -> T:
    """Select the provided points

    Add the provided points, locations or snaps to current selections

    Examples::

        circles_on_arc = (
            cq.Sketch()
            .center_arc(center=(0, 0), radius=10, start_angle=0, arc_size=90, tag="c")
            .push_points("c@0.1", "c@0.5", "c@0.9")
            .circle(1)
        )

    Args:
        pts (Union[Point,str,Location]): points to add
        tag (str, optional): feature label. Defaults to None.

    Returns:
        Updated sketch
    """
    push_pts = self.snap_to_vector(pts)
    self._selection = [l if isinstance(l, Location) else Location(l) for l in push_pts]

    if tag:
        self._tag(self._selection[:], tag)

    return self


Sketch.push_points = _push_points_sketch


def _bounding_box_sketch(
    self: T,
    mode: "Modes" = "a",
    # mode: Mode = Mode.ADDITION,
    tag: Optional[str] = None,
) -> T:
    """Bounding Box

    Create bounding box(s) around selected features. These bounding boxes can
    be used to directly construct shapes or to locate other shapes.

    Examples::

        mickey = (
            cq.Sketch()
            .circle(10)
            .faces()
            .bounding_box(tag="bb", mode="c")
            .faces(tag="bb")
            .vertices(">Y")
            .circle(7)
            .clean()
        )

        bounding_box_center = (
            cq.Sketch()
            .segment((0, 0), (10, 0))
            .segment((0, 5))
            .close()
            .assemble(tag="t")
            .faces(tag="t")
            .circle(0.5, mode="s")
            .faces(tag="t")
            .bounding_box(tag="bb", mode="c")
            .faces(tag="bb")
            .rect(1, 1, mode="s")
        )

        circles = (
            cq.Sketch()
            .rarray(40, 40, 2, 2)
            .circle(10)
            .reset()
            .faces()
            .bounding_box(tag="bb", mode="c")
            .vertices(tag="bb")
            .circle(7)
            .clean()
        )

    Args:
        tag (Optional[str], optional): feature label. Defaults to None.

    Returns:
        Updated sketch
    """
    bb_faces = []
    for obj in self._selection:
        bb = obj.BoundingBox()
        vertices = [
            (bb.xmin, bb.ymin),
            (bb.xmin, bb.ymax),
            (bb.xmax, bb.ymax),
            (bb.xmax, bb.ymin),
            (bb.xmin, bb.ymin),
        ]
        bb_faces.append(
            Face.makeFromWires(Wire.makePolygon([Vector(v) for v in vertices]))
        )
    bb_faces_iter = iter(bb_faces)
    self.push([(0, 0)] * len(bb_faces))
    self.each(lambda loc: next(bb_faces_iter).located(loc), mode, tag)
    # self.each(lambda loc: next(bb_faces_iter).located(loc), mode.name.lower()[0:1], tag)

    return self


Sketch.bounding_box = _bounding_box_sketch


# def _hull_sketch(self: T, mode: Modes = "a", tag: Optional[str] = None) -> T:
#     # def _hull_sketch(self: T, mode: Mode = Mode.ADDITION, tag: Optional[str] = None) -> T:
#     """
#     Generate a convex hull from current selection or all objects.
#     """

#     hull_edges = []
#     for el in self._selection:
#         if isinstance(el, Edge):
#             hull_edges.append(el)
#         elif isinstance(el, (Face, Wire)):
#             hull_edges.extend(el.Edges())
#     if hull_edges:
#         rv = find_hull(hull_edges)
#     else:
#         raise ValueError("No objects available for hull construction")

#     self.face(rv, mode=mode, tag=tag, ignore_selection=bool(self._selection))

#     return self


# Sketch.hull = _hull_sketch

"""

Wire extensions: makeRect(), makeNonPlanarFace(), projectToShape(), embossToShape()

"""


def _makeRect(
    width: float, height: float, center: Vector, normal: Vector, xDir: Vector = None
) -> "Wire":
    """Make Rectangle

    Make a Rectangle centered on center with the given normal

    Args:
        width (float): width (local X)
        height (float): height (local Y)
        center (Vector): rectangle center point
        normal (Vector): rectangle normal
        xDir (Vector, optional): x direction. Defaults to None.

    Returns:
        Wire: The centered rectangle
    """
    corners_local = [
        (width / 2, height / 2),
        (width / 2, -height / 2),
        (-width / 2, -height / 2),
        (-width / 2, height / 2),
        (width / 2, height / 2),
    ]
    if xDir is None:
        user_plane = Plane(origin=center, normal=normal)
    else:
        user_plane = Plane(origin=center, xDir=xDir, normal=normal)
    corners_world = [user_plane.toWorldCoords(c) for c in corners_local]
    return Wire.makePolygon(corners_world)


Wire.makeRect = _makeRect


def makeNonPlanarFace(
    exterior: Union["Wire", list["Edge"]],
    surfacePoints: list["VectorLike"] = None,
    interiorWires: list["Wire"] = None,
) -> "Face":
    """Create Non-Planar Face

    Create a potentially non-planar face bounded by exterior (wire or edges),
    optionally refined by surfacePoints with optional holes defined by
    interiorWires.

    Args:
        exterior: Perimeter of face
        surfacePoints: Points on the surface that refine the shape. Defaults to None.
        interiorWires: Hole(s) in the face. Defaults to None.

    Raises:
        RuntimeError: Opencascade core exceptions building face

    Returns:
        Non planar face
    """

    if surfacePoints:
        surface_points = [Vector(p) for p in surfacePoints]
    else:
        surface_points = None

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
    if isinstance(exterior, Wire):
        outside_edges = exterior.Edges()
    else:
        outside_edges = exterior
    for edge in outside_edges:
        surface.Add(edge.wrapped, GeomAbs_C0)

    try:
        surface.Build()
        surface_face = Face(surface.Shape())
    except (StdFail_NotDone, Standard_NoSuchObject) as e:
        raise RuntimeError(
            "Error building non-planar face with provided exterior"
        ) from e
    if surface_points:
        for pt in surface_points:
            surface.Add(gp_Pnt(*pt.toTuple()))
        try:
            surface.Build()
            surface_face = Face(surface.Shape())
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
            surface_face = Face(makeface_object.Face())
        except StdFail_NotDone as e:
            raise RuntimeError(
                "Error adding interior hole in non-planar face with provided interiorWires"
            ) from e

    surface_face = surface_face.fix()
    if not surface_face.isValid():
        raise RuntimeError("non planar face is invalid")

    return surface_face


def _wire_makeNonPlanarFace(
    self,
    surfacePoints: list["Vector"] = None,
    interiorWires: list["Wire"] = None,
) -> "Face":
    """Create Non-Planar Face with perimeter Wire

    Create a potentially non-planar face bounded by exterior Wire,
    optionally refined by surfacePoints with optional holes defined by
    interiorWires.

    The **surfacePoints** parameter can be used to refine the resulting Face. If no
    points are provided a single central point will be used to help avoid the
    creation of a planar face.

    Args:
        surfacePoints: Points on the surface that refine the shape. Defaults to None.
        interiorWires: Hole(s) in the face. Defaults to None.

    Raises:
        RuntimeError: Opencascade core exceptions building face

    Returns:
        Non planar face
    """
    return makeNonPlanarFace(self, surfacePoints, interiorWires)


Wire.makeNonPlanarFace = _wire_makeNonPlanarFace


def _projectWireToShape(
    self,
    targetObject: "Shape",
    direction: "VectorLike" = None,
    center: "VectorLike" = None,
) -> list["Wire"]:
    """Project Wire

    Project a Wire onto a Shape generating new Wires on the surfaces of the object
    one and only one of `direction` or `center` must be provided. Note that one or
    more wires may be generated depending on the topology of the target object and
    location/direction of projection.

    To avoid flipping the normal of a face built with the projected wire the orientation
    of the output wires are forced to be the same as self.

    Args:
        targetObject: Object to project onto
        direction: Parallel projection direction. Defaults to None.
        center: Conical center of projection. Defaults to None.

    Raises:
        ValueError: Only one of direction or center must be provided

    Returns:
        Projected wire(s)
    """
    if not (direction is None) ^ (center is None):
        raise ValueError("One of either direction or center must be provided")
    if direction is not None:
        direction_vector = Vector(direction).normalized()
        center_point = None
    else:
        direction_vector = None
        center_point = Vector(center)

    # Project the wire on the target object
    if not direction_vector is None:
        projection_object = BRepProj_Projection(
            self.wrapped,
            Shape.cast(targetObject.wrapped).wrapped,
            gp_Dir(*direction_vector.toTuple()),
        )
    else:
        projection_object = BRepProj_Projection(
            self.wrapped,
            Shape.cast(targetObject.wrapped).wrapped,
            gp_Pnt(*center_point.toTuple()),
        )

    # Generate a list of the projected wires with aligned orientation
    output_wires = []
    target_orientation = self.wrapped.Orientation()
    while projection_object.More():
        projected_wire = projection_object.Current()
        if target_orientation == projected_wire.Orientation():
            output_wires.append(Wire(projected_wire))
        else:
            output_wires.append(Wire(projected_wire.Reversed()))
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


Wire.projectToShape = _projectWireToShape


def _embossWireToShape(
    self,
    targetObject: "Shape",
    surfacePoint: "VectorLike",
    surfaceXDirection: "VectorLike",
    tolerance: float = 0.01,
) -> "Wire":
    """Emboss Wire on target object

    Emboss an Wire on the XY plane onto a Shape while maintaining
    original wire dimensions where possible.

    .. image:: embossWire.png

    The embossed wire can be used to build features as:

    .. image:: embossFeature.png

    with the `sweep() <https://cadquery.readthedocs.io/en/latest/_modules/cadquery/occ_impl/shapes.html#Solid.sweep>`_ method.

    Args:
        targetObject: Object to emboss onto
        surfacePoint: Point on target object to start embossing
        surfaceXDirection: Direction of X-Axis on target object
        tolerance: maximum allowed error in embossed wire length. Defaults to 0.01.

    Raises:
        RuntimeError: Embosses wire is invalid

    Returns:
        Embossed wire
    """
    import warnings

    # planar_edges = self.Edges()
    planar_edges = self.sortedEdges()
    for i, planar_edge in enumerate(planar_edges[:-1]):
        if (
            planar_edge.positionAt(1) - planar_edges[i + 1].positionAt(0)
        ).Length > tolerance:
            warnings.warn("Edges in provided wire are not sequential - emboss may fail")
            logging.warning(
                "Edges in provided wire are not sequential - emboss may fail"
            )
    planar_closed = self.IsClosed()
    logging.debug(f"embossing wire with {len(planar_edges)} edges")
    edges_in = TopTools_HSequenceOfShape()
    wires_out = TopTools_HSequenceOfShape()

    # Need to keep track of the separation between adjacent edges
    first_start_point = None
    last_end_point = None
    edge_separatons = []
    surface_point = Vector(surfacePoint)
    surface_x_direction = Vector(surfaceXDirection)

    # If the wire doesn't start at the origin, create an embossed construction line to get
    # to the beginning of the first edge
    if planar_edges[0].positionAt(0) == Vector(0, 0, 0):
        edge_surface_point = surface_point
        planar_edge_end_point = Vector(0, 0, 0)
    else:
        construction_line = Edge.makeLine(
            Vector(0, 0, 0), planar_edges[0].positionAt(0)
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
        gap_edge = Edge.makeSpline(
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
    embossed_wire = Wire(embossed_wires[0])

    if planar_closed and not embossed_wire.IsClosed():
        embossed_wire.close()
        logging.debug(
            f"embossed wire was not closed, did fixing succeed: {embossed_wire.IsClosed()}"
        )

    embossed_wire = embossed_wire.fix()

    if not embossed_wire.isValid():
        raise RuntimeError("embossed wire is not valid")

    return embossed_wire


Wire.embossToShape = _embossWireToShape


def _sortedEdges_wire(self, tolerance: float = 1e-5):
    """Edges sorted by position

    Extract the edges from the wire and sort them such that the end of one
    edge is within tolerance of the start of the next edge

    Args:
        tolerance (float, optional): Max separation between sequential edges.
            Defaults to 1e-5.

    Raises:
        ValueError: Wire is disjointed

    Returns:
        list(Edge): Edges sorted by position
    """
    unsorted_edges = self.Edges()
    sorted_edges = [unsorted_edges.pop(0)]
    while unsorted_edges:
        found = False
        for i in range(len(unsorted_edges)):
            if (
                sorted_edges[-1].positionAt(1) - unsorted_edges[i].positionAt(0)
            ).Length < tolerance:
                sorted_edges.append(unsorted_edges.pop(i))
                found = True
                break
        if not found:
            raise ValueError("Edge segments are separated by tolerance or more")

    return sorted_edges


Wire.sortedEdges = _sortedEdges_wire


def _distribute_locations(
    self: Union["Wire", "Edge"],
    count: int,
    start: float = 0.0,
    stop: float = 1.0,
    positions_only: bool = False,
) -> list[Location]:
    """Distribute Locations

    Distribute locations along edge or wire.

    Args:
        count (int): Number of locations to generate
        start (float, optional): position along Edge|Wire to start. Defaults to 0.0.
        stop (float, optional): position along Edge|Wire to end. Defaults to 1.0.
        positions_only (bool, optional): only generate position not orientation. Defaults to False.

    Raises:
        ValueError: count must be two or greater

    Returns:
        list[Location]: locations distributed along Edge|Wire
    """
    if count < 2:
        raise ValueError("count must be two or greater")

    t_values = [start + i * (stop - start) / (count - 1) for i in range(count)]

    locations = []
    if positions_only:
        locations.extend(Location(v) for v in self.positions(t_values))
    else:
        locations.extend(self.locations(t_values, planar=True))
    return locations


Wire.distributeLocations = _distribute_locations

"""

Edge extensions: projectToShape(), embossToShape()

"""
Edge.distributeLocations = _distribute_locations


def _projectEdgeToShape(
    self,
    targetObject: "Shape",
    direction: "VectorLike" = None,
    center: "VectorLike" = None,
) -> list["Edge"]:
    """Project Edge

    Project an Edge onto a Shape generating new Wires on the surfaces of the object
    one and only one of `direction` or `center` must be provided. Note that one or
    more wires may be generated depending on the topology of the target object and
    location/direction of projection.

    To avoid flipping the normal of a face built with the projected wire the orientation
    of the output wires are forced to be the same as self.

    Args:
        targetObject: Object to project onto
        direction: Parallel projection direction. Defaults to None.
        center: Conical center of projection. Defaults to None.

    Raises:
        ValueError: Only one of direction or center must be provided

    Returns:
        Projected Edge(s)
    """
    wire = Wire.assembleEdges([self])
    projected_wires = wire.projectToShape(targetObject, direction, center)
    projected_edges = [w.Edges()[0] for w in projected_wires]
    return projected_edges


Edge.projectToShape = _projectEdgeToShape


def _embossEdgeToShape(
    self,
    targetObject: "Shape",
    surfacePoint: "VectorLike",
    surfaceXDirection: "VectorLike",
    tolerance: float = 0.01,
) -> "Edge":
    """Emboss Edge on target object

    Emboss an Edge on the XY plane onto a Shape while maintaining
    original edge dimensions where possible.

    Args:
        targetObject: Object to emboss onto
        surfacePoint: Point on target object to start embossing
        surfaceXDirection: Direction of X-Axis on target object
        tolerance: maximum allowed error in embossed edge length

    Returns:
        Embossed edge
    """

    # Algorithm - piecewise approximation of points on surface -> generate spline:
    # - successively increasing the number of points to emboss
    #     - create local plane at current point given surface normal and surface x direction
    #     - create new approximate point on local plane from next planar point
    #     - get global position of next approximate point
    #     - using current normal and next approximate point find next surface intersection point and normal
    # - create spline from points
    # - measure length of spline
    # - repeat with more points unless within target tolerance

    def find_point_on_surface(
        current_surface_point: Vector,
        current_surface_normal: Vector,
        planar_relative_position: Vector,
    ) -> Vector:
        """
        Given a 2D relative position from a surface point, find the closest point on the surface.
        """
        segment_plane = Plane(
            origin=current_surface_point,
            xDir=surface_x_direction,
            normal=current_surface_normal,
        )
        target_point = segment_plane.toWorldCoords(planar_relative_position.toTuple())
        (next_surface_point, next_surface_normal) = targetObject.findIntersection(
            point=target_point, direction=target_point - target_object_center
        )[0]
        return (next_surface_point, next_surface_normal)

    surface_x_direction = Vector(surfaceXDirection)

    planar_edge_length = self.Length()
    planar_edge_closed = self.IsClosed()
    target_object_center = targetObject.Center()
    loop_count = 0
    subdivisions = 2
    length_error = sys.float_info.max

    while length_error > tolerance and loop_count < 8:

        # Initialize the algorithm by priming it with the start of Edge self
        surface_origin = Vector(surfacePoint)
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
        embossed_edge = Edge.makeSpline(
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


Edge.embossToShape = _embossEdgeToShape

"""

Shape extensions: transformed(), findIntersection(), projectText(), embossText(), makeFingerJointFaces(),
                  maxFillet(), _apply_transform(), clean(), fix(), located(), moved()

"""


def _transformed(
    self, rotate: VectorLike = (0, 0, 0), offset: VectorLike = (0, 0, 0)
) -> "Shape":
    """Transform Shape

    Rotate and translate the Shape by the three angles (in degrees) and offset.
    Functions exactly like the Workplane.transformed() method but for Shapes.

    Args:
        rotate (VectorLike, optional): 3-tuple of angles to rotate, in degrees. Defaults to (0, 0, 0).
        offset (VectorLike, optional): 3-tuple to offset. Defaults to (0, 0, 0).

    Returns:
        Shape: transformed object
    """

    # Convert to a Vector of radians
    rotate_vector = Vector(rotate).multiply(math.pi / 180.0)
    # Compute rotation matrix.
    t_rx = gp_Trsf()
    t_rx.SetRotation(gp_Ax1(gp_Pnt(0, 0, 0), gp_Dir(1, 0, 0)), rotate_vector.x)
    t_ry = gp_Trsf()
    t_ry.SetRotation(gp_Ax1(gp_Pnt(0, 0, 0), gp_Dir(0, 1, 0)), rotate_vector.y)
    t_rz = gp_Trsf()
    t_rz.SetRotation(gp_Ax1(gp_Pnt(0, 0, 0), gp_Dir(0, 0, 1)), rotate_vector.z)
    t_o = gp_Trsf()
    t_o.SetTranslation(Vector(offset).wrapped)
    return self._apply_transform(t_o * t_rx * t_ry * t_rz)


Shape.transformed = _transformed


def shape_apply_transform(self: "Shape", Tr: gp_Trsf) -> "Shape":
    """_apply_transform

    Apply the provided transformation matrix to a copy of Shape

    Args:
        Tr (gp_Trsf): transformation matrix

    Returns:
        Shape: copy of transformed Shape
    """
    shape_copy: "Shape" = self.copy()
    transformed_shape = BRepBuilderAPI_Transform(shape_copy.wrapped, Tr, True).Shape()
    shape_copy.wrapped = downcast(transformed_shape)
    return shape_copy


Shape._apply_transform = shape_apply_transform


def shape_copy(self: "Shape", mesh: bool = False) -> "Shape":
    """
    Creates a new object that is a copy of this object.
    """
    # The wrapped object is a OCCT TopoDS_Shape which can't be pickled or copied
    # with the standard python copy/deepcopy, so create a deepcopy 'memo' with this
    # value already copied which causes deepcopy to skip it.
    memo = {id(self.wrapped): downcast(BRepBuilderAPI_Copy(self.wrapped, True, mesh).Shape())}
    copy_of_shape = copy.deepcopy(self, memo)
    return copy_of_shape


Shape.copy = shape_copy


def shape_clean(self: "Shape") -> "Shape":
    """clean - remove internal edges"""
    # Try BRepTools.RemoveInternals here
    # shape_copy: "Shape" = self.copy()
    # upgrader = ShapeUpgrade_UnifySameDomain(shape_copy.wrapped, True, True, True)
    # upgrader.AllowInternalEdges(False)
    # upgrader.Build()
    # shape_copy.wrapped = downcast(upgrader.Shape())
    # return shape_copy
    upgrader = ShapeUpgrade_UnifySameDomain(self.wrapped, True, True, True)
    upgrader.AllowInternalEdges(False)
    upgrader.Build()
    self.wrapped = downcast(upgrader.Shape())
    return self


Shape.clean = shape_clean


def shape_fix(self: "Shape") -> "Shape":
    """fix - try to fix shape if not valid"""
    if not self.isValid():
        shape_copy: "Shape" = self.copy()
        shape_copy.wrapped = fix(self.wrapped)

        return shape_copy

    return self


Shape.fix = shape_fix


def shape_located(self: "Shape", loc: Location) -> "Shape":
    """located

    Apply a location in absolute sense to a copy of self

    Args:
        loc (Location): new absolute location

    Returns:
        Shape: copy of Shape at location
    """
    shape_copy: "Shape" = self.copy()
    shape_copy.wrapped.Location(loc.wrapped)
    return shape_copy


Shape.located = shape_located


def shape_moved(self: "Shape", loc: Location) -> "Shape":
    """moved

    Apply a location in relative sense (i.e. update current location) to a copy of self

    Args:
        loc (Location): new location relative to current location

    Returns:
        Shape: copy of Shape moved to relative location
    """
    shape_copy: "Shape" = self.copy()
    shape_copy.wrapped = downcast(shape_copy.wrapped.Moved(loc.wrapped))
    return shape_copy


Shape.moved = shape_moved


def _findIntersection(
    self, point: "Vector", direction: "Vector"
) -> list[tuple["Vector", "Vector"]]:
    """Find point and normal at intersection

    Return both the point(s) and normal(s) of the intersection of the line and the shape

    Args:
        point: point on intersecting line
        direction: direction of intersecting line

    Returns:
        Point and normal of intersection
    """
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
        intersections.append((Face(intersectMaker.Face()), Vector(interPt), distance))
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


Shape.findIntersection = _findIntersection


def _projectText(
    self,
    txt: str,
    fontsize: float,
    depth: float,
    path: Union["Wire", "Edge"],
    font: str = "Arial",
    fontPath: Optional[str] = None,
    kind: Literal["regular", "bold", "italic"] = "regular",
    valign: Literal["center", "top", "bottom"] = "center",
    start: float = 0,
) -> "Compound":
    """Projected 3D text following the given path on Shape

    Create 3D text using projection by positioning each face of
    the planar text normal to the shape along the path and projecting
    onto the surface. If depth is not zero, the resulting face is
    thickened to the provided depth.

    Note that projection may result in text distortion depending on
    the shape at a position along the path.

    .. image:: projectText.png

    Args:
        txt: Text to be rendered
        fontsize: Size of the font in model units
        depth: Thickness of text, 0 returns a Face object
        path: Path on the Shape to follow
        font: Font name. Defaults to "Arial".
        fontPath: Path to font file. Defaults to None.
        kind: Font type - one of "regular", "bold", "italic". Defaults to "regular".
        valign: Vertical Alignment - one of "center", "top", "bottom". Defaults to "center".
        start: Relative location on path to start the text. Defaults to 0.

    Returns:
        The projected text
    """

    path_length = path.Length()
    shape_center = self.Center()

    # Create text faces
    text_faces = (
        Workplane("XY")
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
        surface_normal_plane = Plane(
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

    return Compound.makeCompound(projected_text)


Shape.projectText = _projectText


def _embossText(
    self,
    txt: str,
    fontsize: float,
    depth: float,
    path: Union["Wire", "Edge"],
    font: str = "Arial",
    fontPath: Optional[str] = None,
    kind: Literal["regular", "bold", "italic"] = "regular",
    valign: Literal["center", "top", "bottom"] = "center",
    start: float = 0,
    tolerance: float = 0.1,
) -> "Compound":
    """Embossed 3D text following the given path on Shape

    Create 3D text by embossing each face of the planar text onto
    the shape along the path. If depth is not zero, the resulting
    face is thickened to the provided depth.

    .. image:: embossText.png

    Args:
        txt: Text to be rendered
        fontsize: Size of the font in model units
        depth: Thickness of text, 0 returns a Face object
        path: Path on the Shape to follow
        font: Font name. Defaults to "Arial".
        fontPath: Path to font file. Defaults to None.
        kind: Font type - one of "regular", "bold", "italic". Defaults to "regular".
        valign: Vertical Alignment - one of "center", "top", "bottom". Defaults to "center".
        start: Relative location on path to start the text. Defaults to 0.

    Returns:
        The embossed text
    """

    path_length = path.Length()
    shape_center = self.Center()

    # Create text faces
    # text_faces = (
    #     Workplane("XY")
    #     .text(
    #         txt,
    #         fontsize,
    #         1,
    #         font=font,
    #         fontPath=fontPath,
    #         kind=kind,
    #         halign="left",
    #         valign=valign,
    #     )
    #     .faces("<Z")
    #     .vals()
    # )
    text_faces = Compound.make2DText(
        txt, fontsize, font, fontPath, kind, "left", valign, start
    ).Faces()

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
                self, path_position, path_tangent, tolerance=tolerance
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

    return Compound.makeCompound(embossed_text)


Shape.embossText = _embossText


def _makeFingerJointFaces_shape(
    self: "Shape",
    fingerJointEdges: list["Edge"],
    materialThickness: float,
    targetFingerWidth: float,
    kerfWidth: float = 0.0,
) -> list["Face"]:
    """makeFingerJointFaces

    Extract Faces from the given Shape (Solid or Compound) and create Faces with finger
    joints cut into the given Edges.

    Args:
        self (Shape): the base shape defining the finger jointed object
        fingerJointEdges (list[Edge]): the Edges to convert to finger joints
        materialThickness (float): thickness of the notch from edge
        targetFingerWidth (float): approximate with of notch - actual finger width
            will be calculated such that there are an integer number of fingers on Edge
        kerfWidth (float, optional): Extra size to add (or subtract) to account
            for the kerf of the laser cutter. Defaults to 0.0.

    Raises:
        ValueError: provide Edge is not shared by two Faces

    Returns:
        list[Face]: faces with finger joint cut into selected edges
    """
    # Store the faces for modification
    working_faces = self.Faces()
    working_face_areas = [f.Area() for f in working_faces]

    # Build relationship between vertices, edges and faces
    edge_adjacency = {}  # Faces that share this edge (2)
    edge_vertex_adjacency = {}  # Faces that share this vertex
    for common_edge in fingerJointEdges:
        adjacent_face_indices = [
            i for i, face in enumerate(working_faces) if common_edge in face.Edges()
        ]
        if adjacent_face_indices:
            if len(adjacent_face_indices) != 2:
                raise ValueError("Edge is invalid")
            edge_adjacency[common_edge] = adjacent_face_indices
        for v in common_edge.Vertices():
            if v in edge_vertex_adjacency:
                edge_vertex_adjacency[v].update(adjacent_face_indices)
            else:
                edge_vertex_adjacency[v] = set(adjacent_face_indices)

    # External edges need tabs cut from the face while internal edges need extended tabs.
    # Faces that aren't perpendicular need the tab depth to be calculated based on the
    # angle between the faces. To facilitate this, calculate the angle between faces
    # and determine if this is an internal corner.
    finger_depths = {}
    external_corners = {}
    for common_edge, adjacent_face_indices in edge_adjacency.items():
        face_centers = [working_faces[i].Center() for i in adjacent_face_indices]
        face_normals = [
            working_faces[i].normalAt(working_faces[i].Center())
            for i in adjacent_face_indices
        ]
        internal_edge_reference_plane = cq.Plane(
            origin=face_centers[0], normal=face_normals[0]
        )
        localized_opposite_center = internal_edge_reference_plane.toLocalCoords(
            face_centers[1]
        )
        external_corners[common_edge] = localized_opposite_center.z < 0
        corner_angle = abs(
            face_normals[0].getSignedAngle(face_normals[1], common_edge.tangentAt(0))
        )
        finger_depths[common_edge] = materialThickness * max(
            math.sin(corner_angle),
            (
                math.sin(corner_angle)
                + (math.cos(corner_angle) - 1) * math.tan(math.pi / 2 - corner_angle)
            ),
        )

    # To avoid missing internal corners with open boxes, determine which vertices
    # are adjacent to the open face(s)
    vertices_with_internal_edge = {}
    for e in fingerJointEdges:
        for v in e.Vertices():
            if v in vertices_with_internal_edge:
                vertices_with_internal_edge[v] = (
                    vertices_with_internal_edge[v] or not external_corners[e]
                )
            else:
                vertices_with_internal_edge[v] = not external_corners[e]
    open_internal_vertices = {}
    for i, f in enumerate(working_faces):
        for v in f.Vertices():
            if vertices_with_internal_edge[v]:
                if i not in edge_vertex_adjacency[v]:
                    if v in open_internal_vertices:
                        open_internal_vertices[v].add(i)
                    else:
                        open_internal_vertices[v] = set([i])

    # Keep track of the numbers of fingers/notches in the corners
    corner_face_counter = {}

    # Make complimentary tabs in faces adjacent to common edges
    for common_edge, adjacent_face_indices in edge_adjacency.items():
        # For cosmetic reasons, try to be consistent in the notch pattern
        # by using the face area as the selection factor
        primary_face_index = adjacent_face_indices[0]
        secondary_face_index = adjacent_face_indices[1]
        if (
            working_face_areas[primary_face_index]
            > working_face_areas[secondary_face_index]
        ):
            primary_face_index, secondary_face_index = (
                secondary_face_index,
                primary_face_index,
            )

        for i in [primary_face_index, secondary_face_index]:
            working_faces[i] = working_faces[i].makeFingerJoints(
                common_edge,
                finger_depths[common_edge],
                targetFingerWidth,
                corner_face_counter,
                open_internal_vertices,
                alignToBottom=i == primary_face_index,
                externalCorner=external_corners[common_edge],
                faceIndex=i,
            )

    # Determine which faces have tabs
    tabbed_face_indices = set(
        i for face_list in edge_adjacency.values() for i in face_list
    )
    tabbed_faces = [working_faces[i] for i in tabbed_face_indices]

    # If kerf compensation is requested, increase the outer and decrease inner sizes
    if kerfWidth != 0.0:
        tabbed_faces = [
            Face.makeFromWires(
                f.outerWire().offset2D(kerfWidth / 2)[0],
                [i.offset2D(-kerfWidth / 2)[0] for i in f.innerWires()],
            )
            for f in tabbed_faces
        ]

    return tabbed_faces


Shape.makeFingerJointFaces = _makeFingerJointFaces_shape


def _maxFillet(
    self: "Shape",
    edgeList: Iterable["Edge"],
    tolerance=0.1,
    maxIterations: int = 10,
) -> float:
    """Find Maximum Fillet Size

    Find the largest fillet radius for the given Shape and Edges with a
    recursive binary search.

    Args:
        edgeList (Iterable[Edge]): a list of Edge objects, which must belong to this solid
        tolerance (float, optional): maximum error from actual value. Defaults to 0.1.
        maxIterations (int, optional): maximum number of recursive iterations. Defaults to 10.

    Raises:
        RuntimeError: failed to find the max value
        ValueError: the provided Shape is invalid

    Returns:
        float: maximum fillet radius

    As an example:
        max_fillet_radius = my_shape.maxFillet(shape_edges)
    or:
        max_fillet_radius = my_shape.maxFillet(shape_edges, tolerance=0.5, maxIterations=8)

    """

    def __maxFillet(window_min: float, window_max: float, current_iteration: int):
        window_mid = (window_min + window_max) / 2

        if current_iteration == maxIterations:
            raise RuntimeError(
                f"Failed to find the max value within {tolerance} in {maxIterations}"
            )

        # Do these numbers work? - if not try with the smaller window
        try:
            if not self.fillet(window_mid, edgeList).isValid():
                raise StdFail_NotDone
        except StdFail_NotDone:
            return __maxFillet(window_min, window_mid, current_iteration + 1)

        # These numbers work, are they close enough? - if not try larger window
        if window_mid - window_min <= tolerance:
            return window_mid
        else:
            return __maxFillet(window_mid, window_max, current_iteration + 1)

    if not self.isValid():
        raise ValueError("Invalid Shape")
    max_radius = __maxFillet(0.0, 2 * self.BoundingBox().DiagonalLength, 0)

    return max_radius


Shape.maxFillet = _maxFillet

"""

Location extensions: __str__(), position(), rotation()

"""


def _location_str(self):
    """To String

    Convert Location to String for display

    Returns:
        Location as String
    """
    loc_tuple = self.toTuple()
    return f"Location: ({str(loc_tuple[0])}, {str(loc_tuple[1])})"


Location.__str__ = _location_str
Location.__repr__ = _location_str


def _location_position(self):
    """Extract Position component

    Returns:
        Vector: Position part of Location
    """
    return Vector(self.toTuple()[0])


Location.position = _location_position


def _location_rotation(self):
    """Extract Rotation component

    Returns:
        Vector: Rotation part of Location
    """
    return Vector(self.toTuple()[1])


Location.rotation = _location_rotation
