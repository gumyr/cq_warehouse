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
import math
from typing import Optional, Literal, Union, Tuple
import cadquery as cq
from cadquery.occ_impl.shapes import VectorLike
from cadquery.cq import T
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
    Vector,
    Vertex,
    Wire,
    Workplane,
    DirectionMinMaxSelector,
)

# from cq_warehouse.fastener import Screw, Nut, Washer

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
from OCP.gp import gp_Pnt, gp_Vec
from OCP.Bnd import Bnd_Box
from OCP.StdFail import StdFail_NotDone
from OCP.Standard import Standard_NoSuchObject
from OCP.BRepIntCurveSurface import BRepIntCurveSurface_Inter
from OCP.gp import gp_Vec, gp_Pnt, gp_Ax1, gp_Dir, gp_Trsf, gp, gp_GTrsf

# Logging configuration - uncomment to enable logs
# logging.basicConfig(
#     filename="cq_warehouse.log",
#     encoding="utf-8",
#     level=logging.DEBUG,
#     format="%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)s - %(funcName)20s() ] - %(message)s",
# )

"""

Assembly extensions: rotate(), translate(), fastenerQuantities(), fastenerLocations()

"""


def _assembly_translate(self, vec: "VectorLike") -> "Assembly":
    """
    Moves the current assembly (without making a copy) by the specified translation vector

    Args:
        vec: The translation vector

    Returns:
        The translated Assembly

    Example:
        plain_assembly.translate((1,2,3))
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
        plain_assembly.rotate((0,0,1),90)
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
    assembly_list = []
    if deep:
        for _name, sub_assembly in self.traverse():
            assembly_list.append(sub_assembly)
    else:
        assembly_list.append(self)

    fasteners = []
    for sub_assembly in assembly_list:
        for value in sub_assembly.metadata.values():
            if isinstance(value, (Screw, Nut, Washer)):
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

    name_to_fastener = {}
    base_assembly_structure = {}
    # Extract a list of only the fasteners from the metadata
    for (name, a) in self.traverse():
        base_assembly_structure[name] = a
        if a.metadata is None:
            continue

        for key, value in a.metadata.items():
            if value == fastener:
                name_to_fastener[key] = value

    fastener_path_locations = {}
    base_assembly_path = self._flatten()
    for assembly_name, _assembly_pointer in base_assembly_path.items():
        for fastener_name in name_to_fastener.keys():
            if fastener_name in assembly_name:
                parents = assembly_name.split("/")
                fastener_path_locations[fastener_name] = [
                    base_assembly_structure[name].loc for name in parents
                ]

    fastener_locations = [
        reduce(lambda l1, l2: l1 * l2, locs)
        for locs in fastener_path_locations.values()
    ]

    return fastener_locations


Assembly.fastenerLocations = _fastener_locations


"""

Plane extensions: toLocalCoords()

"""


def _toLocalCoords(self, obj: Union["Vector", "Shape", "BoundBox"]):
    """Project the provided coordinates onto this plane

    Args:
        obj: an object, vector, or bounding box to convert

    Returns:
        an object of the same type, but converted to local coordinates

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
    elif isinstance(obj, BoundBox):
        global_bottom_left = Vector(obj.xmin, obj.ymin, obj.zmin)
        global_top_right = Vector(obj.xmax, obj.ymax, obj.zmax)
        local_bottom_left = global_bottom_left.transform(self.fG)
        local_top_right = global_top_right.transform(self.fG)
        local_bbox = Bnd_Box(
            gp_Pnt(*local_bottom_left.toTuple()), gp_Pnt(*local_top_right.toTuple())
        )
        return BoundBox(local_bbox)
    else:
        raise ValueError(
            f"Don't know how to convert type {type(obj)} to local coordinates"
        )


Plane.toLocalCoords = _toLocalCoords


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
                      tapHole(), threadedHole(), pushFastenerLocations()

"""


def _textOnPath(
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

    The parameters are largely the same as the ``Workplane.text`` method. The
    ``start`` parameter (normally between 0.0 and 1.0) specify where on the path to
    start the text.

    The path that the text follows is defined by the last Edge or Wire in the
    Workplane stack. Path's defined outside of the Workplane can be used with the
    ``.add(path)`` method.

    .. image:: textOnPath.png

    Args:
        txt: text to be rendered
        fontsize: size of the font in model units
        distance: the distance to extrude or cut, normal to the workplane plane, negative means opposite the normal direction
        start: the relative location on path to start the text, values must be between 0.0 and 1.0
        cut: True to cut the resulting solid from the parent solids if found
        combine: True to combine the resulting solid with parent solids if found
        clean: call :py:meth:`clean` afterwards to have a clean shape
        font: font name
        fontPath: path to font file
        kind: font type

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

    # from .selectors import DirectionMinMaxSelector

    def position_face(orig_face: "Face") -> "Face":
        """
        Reposition a face to the provided path

        Local coordinates are used to calculate the position of the face
        relative to the path. Global coordinates to position the face.
        """
        bbox = self.plane.toLocalCoords(orig_face.BoundingBox())
        face_bottom_center = Vector((bbox.xmin + bbox.xmax) / 2, 0, 0)
        relative_position_on_wire = start + face_bottom_center.x / path_length
        wire_tangent = path.tangentAt(relative_position_on_wire)
        wire_angle = (
            180
            * self.plane.xDir.getSignedAngle(wire_tangent, self.plane.zDir)
            / math.pi
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
        if type(stack_object) == Edge:
            path = self.ctx.pendingEdges.pop(0)
            break
        if type(stack_object) == Wire:
            path = self.ctx.pendingWires.pop(0)
            break

    # Create text on the current workplane
    raw_text = Compound.makeText(
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
        Workplane(raw_text)
        .faces(DirectionMinMaxSelector(self.plane.zDir, False))
        .vals()
    )
    path_length = path.Length()

    # Reposition all of the text faces and re-create 3D text
    faces_on_path = [position_face(f) for f in text_faces]
    result = Compound.makeCompound(
        [Solid.extrudeLinear(f, self.plane.zDir) for f in faces_on_path]
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
    depth: float,
    washers: list["Washer"],
    fit: Optional[Literal["Close", "Normal", "Loose"]] = None,
    material: Optional[Literal["Soft", "Hard"]] = None,
    counterSunk: Optional[bool] = True,
    baseAssembly: Optional[Assembly] = None,
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
        depth: hole depth
        washers: A list of washer instances, can be empty
        fit: one of "Close", "Normal", "Loose" which determines clearance hole diameter. Defaults to None.
        material: on of "Soft", "Hard" which determines tap hole size. Defaults to None.
        counterSunk: Is the fastener countersunk into the part?. Defaults to True.
        baseAssembly: Assembly to add faster to. Defaults to None.
        hand: tap hole twist direction either "right" or "left". Defaults to None.
        simple: tap hole thread complexity selector. Defaults to False.
        clean: execute a clean operation remove extraneous internal features. Defaults to True.

    Raises:
        ValueError: fit or material not in hole_diameters dictionary

    Returns:
        the shape on the workplane stack with a new hole
    """

    # If there is a thread direction, this is a threaded hole
    threaded_hole = not hand is None

    bore_direction = Vector(0, 0, -1)
    origin = Vector(0, 0, 0)

    # Setscrews' countersink_profile is None so check if it exists
    countersink_profile = fastener.countersink_profile(fit)
    if counterSunk and not countersink_profile is None:
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
                        washer.cq_object,
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
                fastener.cq_object,
                loc=hole_loc
                * Location(
                    bore_direction
                    * (head_offset - fastener.length_offset() - washer_thicknesses)
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
            part = part.union(
                thread.cq_object.moved(hole_loc * Location(bore_direction * depth))
            )
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
    baseAssembly: Optional[Assembly] = None,
    clean: Optional[bool] = True,
) -> T:
    """Clearance Hole

    Put a clearance hole in a shape at the provided location

    For more information on how to use clearanceHole() see
    :ref:`Clearance, Tap and Threaded Holes <clearance holes>`.

    Args:
        fastener: A nut or screw instance
        washers: A list of washer instances, can be empty
        fit: one of "Close", "Normal", "Loose" which determines clearance hole diameter. Defaults to None.
        depth: hole depth. Defaults to through part.
        counterSunk: Is the fastener countersunk into the part?. Defaults to True.
        baseAssembly: Assembly to add faster to. Defaults to None.
        clean: execute a clean operation remove extraneous internal features. Defaults to True.

    Returns:
        the shape on the workplane stack with a new clearance hole
    """
    if depth is None:
        depth = self.largestDimension()

    return self.fastenerHole(
        hole_diameters=fastener.clearance_hole_diameters,
        fastener=fastener,
        washers=washers,
        fit=fit,
        depth=depth,
        counterSunk=counterSunk,
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
    baseAssembly: Optional[Assembly] = None,
    clean: Optional[bool] = True,
) -> T:
    """Tap Hole

    Put a tap hole in a shape at the provided location

    For more information on how to use tapHole() see
    :ref:`Clearance, Tap and Threaded Holes <clearance holes>`.

    Args:
        fastener: A nut or screw instance
        washers: A list of washer instances, can be empty
        material: on of "Soft", "Hard" which determines tap hole size. Defaults to None.
        depth: hole depth. Defaults to through part.
        counterSunk: Is the fastener countersunk into the part?. Defaults to True.
        fit: one of "Close", "Normal", "Loose" which determines clearance hole diameter. Defaults to None.
        baseAssembly: Assembly to add faster to. Defaults to None.
        clean: execute a clean operation remove extraneous internal features. Defaults to True.

    Returns:
        the shape on the workplane stack with a new tap hole
    """
    if depth is None:
        depth = self.largestDimension()

    return self.fastenerHole(
        hole_diameters=fastener.tap_hole_diameters,
        fastener=fastener,
        washers=washers,
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
    baseAssembly: Optional[Assembly] = None,
    clean: Optional[bool] = True,
) -> T:
    """Threaded Hole

    Put a threaded hole in a shape at the provided location

    For more information on how to use threadedHole() see
    :ref:`Clearance, Tap and Threaded Holes <clearance holes>`.

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

    Returns:
        the shape on the workplane stack with a new threaded hole
    """
    return self.fastenerHole(
        hole_diameters=fastener.clearance_hole_diameters,
        fastener=fastener,
        washers=washers,
        fit=fit,
        depth=depth,
        counterSunk=counterSunk,
        baseAssembly=baseAssembly,
        hand=hand,
        simple=simple,
        clean=clean,
    )


Workplane.clearanceHole = _clearanceHole
Workplane.tapHole = _tapHole
Workplane.threadedHole = _threadedHole


def _push_fastener_locations(
    self: T,
    fastener: Union["Nut", "Screw"],
    baseAssembly: Assembly,
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
    ns.objects = baseAssembly.fastenerLocations(fastener)
    ns.ctx = self.ctx
    return ns


Workplane.pushFastenerLocations = _push_fastener_locations

"""

Face extensions: thicken(), projectToShape(), embossToShape()

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

    return result


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
    internalFacePoints: list["Vector"] = [],
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
        internalFacePoints: Surface refinement points. Defaults to [].

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
        targetObject, surfacePoint, surfaceXDirection
    )

    # Phase 2 - inner wires
    planar_inner_wires = [
        w
        if w.wrapped.Orientation() != planar_outer_wire_orientation
        else Wire(w.wrapped.Reversed())
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
            planar_grid = Edge.makeLine(
                planar_outer_wire.positionAt(0), internalFacePoints[0]
            )
        else:
            planar_grid = Wire.makePolygon([Vector(v) for v in internalFacePoints])

        embossed_grid = planar_grid.embossToShape(
            targetObject, surfacePoint, surfaceXDirection
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

"""

Wire extensions: makeNonPlanarFace(), projectToShape(), embossToShape()

"""


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

    surface_points = [Vector(p) for p in surfacePoints]

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
        outside_edges = [e.Edge() for e in exterior]
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

    The ``surfacePoints`` parameter can be used to refine the resulting Face. If no
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

    with the ``sweep`` method.

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
    planar_edges = self.Edges()
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

"""

Edge extensions: projectToShape(), embossToShape()

"""


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
    return self._projectWireToShape(targetObject, direction, center)


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

Shape extensions: findIntersection(), projectText(), embossText()

"""


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

    return Compound.makeCompound(embossed_text)


Shape.embossText = _embossText

"""

Location extensions: __str__()

"""


def _location_str(self):
    """To String

    Convert Location to String for display

    Returns:
        Location as String
    """
    loc_tuple = self.toTuple()
    return f"({str(loc_tuple[0])}, {str(loc_tuple[1])})"


Location.__str__ = _location_str
