"""

Dimension lines for documentation of cadquery designs

name: drafting.py
by:   Gumyr
date: June 28th 2021

desc: A class used to document cadquery designs by providing several methods
      that create objects that can be included into the design illustrating
      marked dimension_lines.

license:

    Copyright 2021 Gumyr

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
from math import sqrt, cos, sin, pi, floor, log2, gcd
from typing import overload, Union, Tuple, Literal
from numpy import arange
import cadquery as cq

MM = 1
INCH = 25.4 * MM

# import cProfile
# import pstats
# TODO: label_norm = (1,0,0) fails
# TODO: location and point_at should accept vertex - done
# TODO: callout to get a path input - done
# TODO: add a flag to Draft to control display of units - done
# TODO: add tolerances - done
# TODO: flatten text - faces("<Z") eliminates text, made thinner
# TODO: path point pair to list and polyline - done
# TODO: add + and - methods to vertex - done
# TODO: handle text too large
# TODO: add fonts and styles to text
# TODO: fix polyline

VectorLike = Union[Tuple[float, float], Tuple[float, float, float], cq.Vector]


class Draft:
    """
    Create 3D engineering dimension_line lines for documenting cadquery designs

    The class stores the style descriptor for the methods

    Methods
    -------
    dimension_line
    extension_line
    callout
    number_with_units
    arrow_head
    line_segment

    """

    unit_LUT = {"metric": "mm", "imperial": '"'}

    def __init__(
        self,
        font_size: float = 5.0,
        color: cq.Color = None,
        arrow_diameter: float = None,
        arrow_length: float = None,
        label_normal: VectorLike = None,
        units: Literal["metric", "imperial"] = "metric",
        number_display: Literal["decimal", "fraction"] = "decimal",
        display_units: bool = True,
        decimal_precision: int = 2,
        fractional_precision: int = 64,
    ):
        self.font_size = font_size
        self.color = color if color is not None else cq.Color(0.25, 0.25, 0.25)
        self.arrow_diameter = arrow_diameter if arrow_diameter is not None else 1
        self.arrow_length = arrow_length if arrow_length is not None else 3
        self.label_norm = (
            cq.Vector(0, 0, 1)
            if label_normal is None
            else cq.Vector(label_normal).normalized()
        )
        if units in ["metric", "imperial"]:
            self.units = units
        else:
            raise ValueError(f'units must be one of {"metric", "imperial"}')
        if number_display in ["decimal", "fraction"]:
            self.number_display = number_display
        else:
            raise ValueError(f'units must be one of {"decimal", "fraction"}')
        self.decimal_precision = decimal_precision
        if log2(fractional_precision).is_integer():
            self.fractional_precision = fractional_precision
        else:
            raise ValueError(
                f"fractional_precision values must be a factor of 2, {fractional_precision} provided"
            )
        if isinstance(display_units, bool):
            self.display_units = display_units
        else:
            raise TypeError(f"display_units is of type bool not {type(display_units)}")

    @overload
    def number_with_units(self, number: float, tolerance: float = None) -> str:
        ...

    @overload
    def number_with_units(
        self, number: float, tolerance: tuple[float, float] = None
    ) -> str:
        ...

    def number_with_units(self, number: float, tolerance=None) -> str:
        """ Convert a raw number to a unit of measurement string based on the class settings """

        def simplify_fraction(numerator: int, denominator: int) -> tuple[int, int]:
            greatest_common_demoninator = gcd(numerator, denominator)
            return (
                int(numerator / greatest_common_demoninator),
                int(denominator / greatest_common_demoninator),
            )

        unit_str = Draft.unit_LUT[self.units] if self.display_units else ""
        if tolerance is None:
            tolerance_str = ""
        elif isinstance(tolerance, float):
            tolerance_str = f" ±{self.number_with_units(tolerance)}"
        elif (
            isinstance(tolerance, tuple)
            and all(isinstance(t, float) for t in tolerance)
            and len(tolerance) == 2
        ):
            tolerance_str = f" +{self.number_with_units(tolerance[0])} -{self.number_with_units(tolerance[1])}"
        else:
            raise TypeError(
                "tolerance must be a single ± float or a tuple of (+float,-float)"
            )

        if self.units == "metric":
            return_value = (
                f"{number / MM:.{self.decimal_precision}f}{unit_str}{tolerance_str}"
            )
        elif self.number_display == "decimal":
            return_value = (
                f"{number / INCH:.{self.decimal_precision}f}{unit_str}{tolerance_str}"
            )
        else:
            whole_part = floor(number / INCH)
            (numerator, demoninator) = simplify_fraction(
                round((number / INCH - whole_part) * self.fractional_precision),
                self.fractional_precision,
            )
            if whole_part == 0:
                return_value = f"{numerator}/{demoninator}{unit_str}{tolerance_str}"
            else:
                return_value = (
                    f"{whole_part} {numerator}/{demoninator}{unit_str}{tolerance_str}"
                )

        return return_value

    def arrow_head(
        self, path: Union[cq.Edge, cq.Wire], tip_pos: float, tail_pos: float
    ) -> cq.Solid:
        """ Create an arrow head which follows the provided path """

        radius = self.arrow_diameter / 2
        arrow_tip = cq.Wire.assembleEdges(
            [
                cq.Edge.makeCircle(
                    radius=0.0001,
                    pnt=path.positionAt(tip_pos),
                    dir=path.tangentAt(tip_pos),
                )
            ]
        )
        arrow_mid = cq.Wire.assembleEdges(
            [
                cq.Edge.makeCircle(
                    radius=0.4 * radius,
                    pnt=path.positionAt((tail_pos + tip_pos) / 2),
                    dir=path.tangentAt((tail_pos + tip_pos) / 2),
                )
            ]
        )
        arrow_tail = cq.Wire.assembleEdges(
            [
                cq.Edge.makeCircle(
                    radius=radius,
                    pnt=path.positionAt(tail_pos),
                    dir=path.tangentAt(tail_pos),
                )
            ]
        )
        return cq.Solid.makeLoft([arrow_tip, arrow_mid, arrow_tail])

    @staticmethod
    def line_segment(
        path: Union[cq.Edge, cq.Wire], tip_pos: float, tail_pos: float
    ) -> cq.Workplane:
        """ Create a segment of a path between tip and tail (inclusive) """
        if not isinstance(path, (cq.Edge, cq.Wire)):
            raise TypeError("path must be of type cadquery Edge or Wire")
        if not 0.0 <= tip_pos <= 1.0:
            raise ValueError(f"tip_pos value of {tip_pos} is not between 0.0 and 1.0")
        if not 0.0 <= tail_pos <= 1.0:
            raise ValueError(f"tail_pos value of {tail_pos} is not between 0.0 and 1.0")
        sub_path = cq.Edge.makeSpline(
            listOfVector=[
                path.positionAt(t)
                for t in arange(tip_pos, tail_pos + 0.00001, (tail_pos - tip_pos) / 16)
            ],
            tangents=[path.tangentAt(t) for t in [tip_pos, tail_pos]],
        )
        return sub_path

    @overload
    def dimension_line(
        self,
        path: Union[cq.Wire, cq.Edge],
        label: str = None,
        arrow_heads: tuple[bool, bool] = None,
        tolerance: Union[float, tuple[float, float]] = None,
    ) -> cq.Workplane:
        ...

    @overload
    def dimension_line(
        self,
        path: list[Union[cq.Vector, cq.Vertex]],
        label: str = None,
        arrow_heads: tuple[bool, bool] = None,
        tolerance: Union[float, tuple[float, float]] = None,
    ) -> cq.Workplane:
        ...

    def dimension_line(
        self, path, label=None, arrow_heads=None, tolerance=None
    ) -> cq.Workplane:
        """ Create a 3D engineering dimension_line line for documenting CAD designs """

        # Create a wire modelling the path of the dimension lines from a variety of input types
        if isinstance(path, (cq.Edge, cq.Wire)):
            line_path = cq.Wire.assembleEdges([path])
        elif isinstance(path, list):
            if all(isinstance(point, (cq.Vector, tuple)) for point in path):
                line_path = cq.Workplane().polyline([cq.Vector(p) for p in path]).val()
            elif all(isinstance(point, cq.Vertex) for point in path):
                line_path = (
                    cq.Workplane()
                    .polyline([cq.Vector(p.toTuple()) for p in path])
                    .val()
                )
        else:
            raise TypeError(
                "path must be a list of vertex/vector/tuple or either a cq.Edge or cq.Wire"
            )
        arrows = [True, True] if arrow_heads is None else arrow_heads
        line_length = line_path.Length()
        label_str = (
            self.number_with_units(line_length, tolerance) if label is None else label
        )

        # Determine the size of the label on the XY to avoid custom plane rotations
        label_xy_object = cq.Workplane("XY").text(
            txt=label_str, fontsize=self.font_size, distance=self.font_size / 20
        )
        label_length = 2.5 * max([v.X for v in label_xy_object.vertices().vals()])

        # Create a plane aligned with the dimension_line to place the text
        text_plane = cq.Plane(
            origin=cq.Vector(0, 0, 0),
            xDir=line_path.tangentAt(0.5),
            normal=self.label_norm,
        )
        label_object = cq.Workplane(text_plane).text(
            txt=label_str, fontsize=self.font_size, distance=self.font_size / 100
        )

        # Calculate the relative positions along the dimension_line line of the key features
        line_controls = [
            self.arrow_length / line_length if arrows[0] else 0.0,
            0.5 - (label_length / 2) / line_length,
            0.5 + (label_length / 2) / line_length,
            1.0 - self.arrow_length / line_length if arrows[1] else 1.0,
        ]
        if line_controls[0] > line_controls[1] or line_controls[2] > line_controls[3]:
            raise ValueError(
                f'Label "{label_str}" is too large for given dimension_line'
            )

        # Compose an assembly with the component parts of the dimension_line line
        d_line = cq.Assembly(None, name=label_str + "_dimension_line", color=self.color)
        if arrows[0]:
            d_line.add(
                self.arrow_head(line_path, tip_pos=0.0, tail_pos=line_controls[0]),
                name="start_arrow",
            )
        d_line.add(
            Draft.line_segment(
                line_path, tip_pos=line_controls[0], tail_pos=line_controls[1]
            ),
            name="start_line",
        )
        d_line.add(label_object.translate(line_path.positionAt(0.5)), name="label")
        d_line.add(
            Draft.line_segment(
                line_path, tip_pos=line_controls[2], tail_pos=line_controls[3]
            ),
            name="end_line",
        )
        if arrows[1]:
            d_line.add(
                self.arrow_head(line_path, tip_pos=1.0, tail_pos=line_controls[3]),
                name="end_arrow",
            )

        return d_line

    @overload
    def extension_line(
        self,
        object_edge: Union[cq.Wire, cq.Edge],
        offset: float,
        label: str = None,
        tolerance: Union[float, tuple[float, float]] = None,
    ):
        ...

    @overload
    def extension_line(
        self,
        object_edge: list[Union[cq.Vector, cq.Vertex]],
        offset: float,
        label: str = None,
        tolerance: Union[float, tuple[float, float]] = None,
    ):
        ...

    def extension_line(
        self, object_edge, offset: float, label: str = None, tolerance=None
    ):
        """ Create a dimension line with two lines extending outward from the part to dimension """

        # Create a wire modelling the path of the dimension lines from a variety of input types
        if isinstance(object_edge, (cq.Edge, cq.Wire)):
            object_path = cq.Wire.assembleEdges([object_edge])
        elif isinstance(object_edge, list):
            if all(isinstance(point, (cq.Vector, tuple)) for point in object_edge):
                object_path = (
                    cq.Workplane().polyline([cq.Vector(p) for p in object_edge]).val()
                )
            elif all(isinstance(point, cq.Vertex) for point in object_edge):
                object_path = (
                    cq.Workplane()
                    .polyline([cq.Vector(p.toTuple()) for p in object_edge])
                    .val()
                )
        else:
            raise TypeError(
                "object_edge must be a list of vertex/vector/tuple or either a cq.Edge or cq.Wire"
            )

        object_length = object_path.Length()
        extension_tangent = object_path.tangentAt(0).cross(self.label_norm)
        dimension_plane = cq.Plane(
            origin=object_path.positionAt(0),
            xDir=extension_tangent,
            normal=self.label_norm,
        )
        ext_line0 = (
            cq.Workplane(dimension_plane).moveTo(1.5 * MM, 0).lineTo(offset + 3 * MM, 0)
        )
        ext_line1 = (
            cq.Workplane(dimension_plane)
            .moveTo(1.5 * MM, object_length)
            .lineTo(offset + 3 * MM, object_length)
        )

        p0 = ext_line0.val().positionAt(offset / (offset + 3 * MM))
        p1 = ext_line1.val().positionAt(offset / (offset + 3 * MM))
        e_line = cq.Assembly(None, name="extension_line", color=self.color)
        e_line.add(ext_line0, name="extension_line0")
        e_line.add(ext_line1, name="extension_line1")
        e_line.add(
            self.dimension_line(label=label, path=[p0, p1], tolerance=tolerance),
            name="dimension_line",
        )
        return e_line

    @overload
    def callout(
        self,
        label: str,
        tail: Union[VectorLike, cq.Vertex],
        justify: Literal["left", "center", "right"] = "left",
    ):
        ...

    @overload
    def callout(
        self,
        label: str,
        tail: Union[cq.Edge, cq.Wire],
        justify: Literal["left", "center", "right"] = "left",
    ):
        ...

    @overload
    def callout(
        self,
        label: str,
        tail: list[Union[VectorLike, cq.Vertex]],
        justify: Literal["left", "center", "right"] = "left",
    ):
        ...

    def callout(
        self, label: str, tail, justify: Literal["left", "center", "right"] = "left",
    ):
        """ Create a text box that optionally points at something """

        line_path = None
        # Create a wire modelling the path of the tail from a variety of input types
        if isinstance(tail, (cq.Edge, cq.Wire)):
            line_path = cq.Wire.assembleEdges([tail])
            text_origin = line_path.positionAt(0)
        elif isinstance(tail, list):
            if len(tail) > 1:
                if all(isinstance(point, (cq.Vector, tuple)) for point in tail):
                    line_path = (
                        cq.Workplane().polyline([cq.Vector(p) for p in tail]).val()
                    )
                elif all(isinstance(point, cq.Vertex) for point in tail):
                    line_path = (
                        cq.Workplane()
                        .polyline([cq.Vector(p.toTuple()) for p in tail])
                        .val()
                    )
            text_origin = line_path.positionAt(0)
        elif isinstance(tail, (cq.Vector, tuple)):
            text_origin = cq.Vector(tail)
        elif isinstance(tail, cq.Vertex):
            text_origin = cq.Vector(tail.toTuple())
        else:
            raise TypeError(
                "tail must be a point of type Vector/tuple, list of Vertex/Vector/tuple or either a cq.Edge or cq.Wire"
            )

        if justify in ["left", "center", "right"]:
            self.number_display = justify
        else:
            raise ValueError(f'justify must be one of {"left", "center", "right"}')

        text_plane = cq.Plane(
            origin=text_origin, xDir=cq.Vector(1, 0, 0), normal=self.label_norm,
        )
        t_box = cq.Assembly(None, name=label + "_callout", color=self.color)
        label_text = cq.Workplane(text_plane).text(
            txt=label,
            fontsize=self.font_size,
            distance=self.font_size / 100,
            halign=justify,
        )
        t_box.add(label_text, name="callout_label")
        if line_path is not None:
            line_length = line_path.Length()
            t_box.add(
                Draft.line_segment(
                    line_path, tip_pos=1.5 * MM / line_length, tail_pos=1.0
                ),
                name="callout_line",
            )
            t_box.add(
                self.arrow_head(
                    line_path,
                    tip_pos=1.0,
                    tail_pos=1.0 - self.arrow_length / line_length,
                ),
                name="callout_arrow",
            )

        return t_box


def __vertex_add__(
    self, other: Union[cq.Vertex, cq.Vector, Tuple[float, float, float]]
) -> cq.Vertex:
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
    return f"Vertex: ({self.X},{self.Y},{self.Z})"


cq.Vertex.__str__ = __vertex_str__


def _vertex_toVector(self) -> cq.Vector:
    return cq.Vector(self.toTuple())


cq.Vertex.toVector = _vertex_toVector
