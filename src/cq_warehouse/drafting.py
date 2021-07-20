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
from pydantic import BaseModel, PrivateAttr, validator, validate_arguments
from math import floor, log2, gcd
from typing import Union, Tuple, Literal, Optional, ClassVar, Any
from numpy import arange
import cadquery as cq

MM = 1
INCH = 25.4 * MM

# import cProfile
# import pstats
# TODO: label_norm = (1,0,0) fails - done
# TODO: location and point_at should accept vertex - done
# TODO: callout to get a path input - done
# TODO: add a flag to Draft to control display of units - done
# TODO: add tolerances - done
# TODO: flatten text - faces("<Z") eliminates text, made thinner
# TODO: path point pair to list and polyline - done
# TODO: add + and - methods to vertex - done
# TODO: handle text too large - partial, add case 'b'
# TODO: add fonts and styles to text
# TODO: fix polyline: done
# TODO: add arc lines as dimension lines where the label is an angle
# TODO: remove tail_pos from arrow_and_shaft - done
# TODO: factor out label generation and return (label,length)
# TODO: add arrows to extension_line

VectorLike = Union[Tuple[float, float, float], cq.Vector]
PathDescriptor = Union[
    cq.Wire, cq.Edge, list[Union[cq.Vector, cq.Vertex, Tuple[float, float, float]]],
]
PointDescriptor = Union[cq.Vector, cq.Vertex, Tuple[float, float, float]]


class Draft(BaseModel):
    """
    Create 3D engineering dimension_line lines for documenting cadquery designs

    The class stores the style descriptor for the methods

    Methods
    -------
    dimension_line
    extension_line
    callout
    number_with_units
    arrow_and_shaft
    line_segment

    """

    # Class Attributes
    unit_LUT: ClassVar[dict] = {"metric": "mm", "imperial": '"'}

    # Instance Attributes
    font_size: float = 5.0
    color: Optional[cq.Color] = None
    arrow_diameter: float = 1.0
    arrow_length: float = 3.0
    label_normal: Optional[VectorLike] = None
    units: Literal["metric", "imperial"] = "metric"
    number_display: Literal["decimal", "fraction"] = "decimal"
    display_units: bool = True
    decimal_precision: int = 2
    fractional_precision: int = 64

    # Private Attributes
    _label_normal: cq.Vector = PrivateAttr()
    _label_x_dir: cq.Vector = PrivateAttr()

    # Override the __init__ method to set a default color as
    # >>> color: cq.Color = cq.Color(0.25,0.25,0.25)
    # results in
    # >>> TypeError: cannot pickle 'OCP.Quantity.Quantity_ColorRGBA' object
    # and to initialize the normal vector
    def __init__(self, **data: Any):
        super().__init__(**data)
        self._label_normal = (
            cq.Vector(0, 0, 1)
            if self.label_normal is None
            else cq.Vector(self.label_normal).normalized()
        )
        self._label_x_dir = (
            cq.Vector(0, 1, 0)
            if self._label_normal == cq.Vector(1, 0, 0)
            else cq.Vector(1, 0, 0)
        )
        self.color = cq.Color(0.25, 0.25, 0.25) if self.color is None else self.color

    class Config:
        arbitrary_types_allowed = True

    @validator("fractional_precision")
    def fractional_precision_power_two(cls, fractional_precision):
        if not log2(fractional_precision).is_integer():
            raise ValueError(
                f"fractional_precision values must be a factor of 2; provided {fractional_precision}"
            )
        return fractional_precision

    @validate_arguments
    def number_with_units(
        self, number: float, tolerance: Union[float, Tuple[float, float]] = None
    ) -> str:
        """ Convert a raw number to a unit of measurement string based on the class settings """

        def simplify_fraction(numerator: int, denominator: int) -> tuple[int, int]:
            """ Mathimatically simplify a fraction given a numerator and demoninator """
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
        else:
            tolerance_str = f" +{self.number_with_units(tolerance[0])} -{self.number_with_units(tolerance[1])}"

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

    @validate_arguments(config=dict(arbitrary_types_allowed=True))
    def arrow_and_shaft(
        self, path: Union[cq.Edge, cq.Wire], tip_pos: Literal["start", "end"] = "start"
    ) -> cq.Solid:
        """ Create an arrow head which follows the provided path """

        if tip_pos == "start":
            tip = 0.0
            mid = 0.0 + self.arrow_length / (2 * cq.Wire.assembleEdges([path]).Length())
            tail = 0.0 + self.arrow_length / cq.Wire.assembleEdges([path]).Length()
        else:
            tip = 1.0
            mid = 1.0 - self.arrow_length / (2 * cq.Wire.assembleEdges([path]).Length())
            tail = 1.0 - self.arrow_length / cq.Wire.assembleEdges([path]).Length()

        arrow_tip = cq.Wire.assembleEdges(
            [
                cq.Edge.makeCircle(
                    radius=0.0001, pnt=path.positionAt(tip), dir=path.tangentAt(tip),
                )
            ]
        )
        arrow_mid = cq.Wire.assembleEdges(
            [
                cq.Edge.makeCircle(
                    radius=0.2 * self.arrow_diameter,
                    pnt=path.positionAt(mid),
                    dir=path.tangentAt(mid),
                )
            ]
        )
        arrow_tail = cq.Wire.assembleEdges(
            [
                cq.Edge.makeCircle(
                    radius=self.arrow_diameter / 2,
                    pnt=path.positionAt(tail),
                    dir=path.tangentAt(tail),
                )
            ]
        )
        arrow = cq.Assembly(None, name="arrow")
        arrow.add(
            cq.Solid.makeLoft([arrow_tip, arrow_mid, arrow_tail]),
            name="arrow_and_shaft",
        )
        arrow.add(path, name="arrow_shaft")
        return arrow

    @staticmethod
    def line_segment(
        path: Union[cq.Edge, cq.Wire], tip_pos: float, tail_pos: float
    ) -> cq.Workplane:
        """ Create a segment of a path between tip and tail (inclusive) """

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

    @staticmethod
    def path_to_wire(path: PathDescriptor) -> cq.Wire:
        """ Convert a PathDescriptor into a cq.Wire """
        if isinstance(path, (cq.Edge, cq.Wire)):
            path_as_wire = cq.Wire.assembleEdges([path])
        else:
            path_as_wire = cq.Wire.assembleEdges(
                cq.Workplane()
                .polyline(
                    [
                        cq.Vector(p.toTuple())
                        if isinstance(p, cq.Vertex)
                        else cq.Vector(p)
                        for p in path
                    ]
                )
                .vals()
            )
        return path_as_wire

    def label_size(self, label_str: str) -> float:

        label_xy_object = cq.Workplane("XY").text(
            txt=label_str, fontsize=self.font_size, distance=self.font_size / 20
        )
        label_length = 2.25 * max([v.X for v in label_xy_object.vertices().vals()])
        return label_length

    @validate_arguments(config=dict(arbitrary_types_allowed=True))
    def dimension_line(
        self,
        path: PathDescriptor,
        label: str = None,
        arrows: Tuple[bool, bool] = (True, True),
        tolerance: Optional[Union[float, Tuple[float, float]]] = None,
    ) -> cq.Workplane:
        """
        Create a dimension line typically for internal measurements
        There are three options depending on the size of the text and length
        of the dimension line:
        1) The label and arrows fit within the length of the path
        2) The text fit within the path and the arrows go outside
        3) Neither the text nor the arrows fit within the path
        """

        # Create a wire modelling the path of the dimension lines from a variety of input types
        line_wire = Draft.path_to_wire(path)
        line_length = line_wire.Length()

        label_str = (
            self.number_with_units(line_length, tolerance) if label is None else label
        )
        label_length = self.label_size(label_str)

        # Determine the type of this dimension line
        if label_length + len(arrows) * self.arrow_length < line_length:
            type = 1
        elif label_length < line_length:
            type = 2
        else:
            type = 3

        # Calculate the relative positions along the dimension_line line of the key features
        line_controls = [
            0.0,
            0.5 - (label_length / 2) / line_length,
            0.5 + (label_length / 2) / line_length,
            1.0,
        ]
        if line_controls[0] > line_controls[1] or line_controls[2] > line_controls[3]:
            raise ValueError(
                f'Label "{label_str}" is too large for given dimension_line'
            )

        # Compose an assembly with the component parts of the dimension_line line
        d_line = cq.Assembly(None, name=label_str + "_dimension_line", color=self.color)
        if arrows[0]:
            if type == 1:
                start_arrow_line = Draft.line_segment(
                    line_wire, tip_pos=line_controls[0], tail_pos=line_controls[1]
                )
            else:
                start_arrow_line = (
                    cq.Workplane(
                        cq.Plane(
                            origin=line_wire.positionAt(0.0),
                            xDir=line_wire.tangentAt(0.0),
                            normal=self._label_normal,
                        )
                    )
                    .hLineTo(-1.5 * self.font_size)
                    .val()
                )

            d_line.add(
                self.arrow_and_shaft(start_arrow_line, tip_pos="start"),
                name="start_arrow",
            )
        if arrows[1]:
            if type == 1:
                end_arrow_line = Draft.line_segment(
                    line_wire, tip_pos=line_controls[2], tail_pos=line_controls[3]
                )
            else:
                end_arrow_line = (
                    cq.Workplane(
                        cq.Plane(
                            origin=line_wire.positionAt(1.0),
                            xDir=line_wire.tangentAt(1.0),
                            normal=self._label_normal,
                        )
                    )
                    .hLineTo(1.5 * self.font_size)
                    .val()
                )
            d_line.add(
                self.arrow_and_shaft(end_arrow_line, tip_pos="start"), name="end_arrow",
            )
        if type == 1:
            # Create a plane aligned with the dimension_line to place the text
            text_plane = cq.Plane(
                origin=cq.Vector(0, 0, 0),
                xDir=line_wire.tangentAt(0.5),
                normal=self._label_normal,
            )
            label_object = cq.Workplane(text_plane).text(
                txt=label_str, fontsize=self.font_size, distance=self.font_size / 100
            )
            d_line.add(label_object.translate(line_wire.positionAt(0.5)), name="label")
        elif arrows[1]:
            text_plane = cq.Plane(
                origin=cq.Vector(1.5 * MM, 0, 0),
                xDir=end_arrow_line.tangentAt(1.0),
                normal=self._label_normal,
            )
            label_object = cq.Workplane(text_plane).text(
                txt=label_str,
                fontsize=self.font_size,
                distance=self.font_size / 100,
                halign="left",
            )
            d_line.add(
                label_object.translate(end_arrow_line.positionAt(1.0)), name="label"
            )
        elif arrows[0]:
            text_plane = cq.Plane(
                origin=cq.Vector(-1.5 * MM, 0, 0),
                xDir=start_arrow_line.tangentAt(1.0),
                normal=self._label_normal,
            )
            label_object = cq.Workplane(text_plane).text(
                txt=label_str,
                fontsize=self.font_size,
                distance=self.font_size / 100,
                halign="right",
            )
            d_line.add(
                label_object.translate(start_arrow_line.positionAt(1.0)), name="label"
            )
        else:
            pass
        return d_line

    @validate_arguments(config=dict(arbitrary_types_allowed=True))
    def extension_line(
        self,
        object_edge: PathDescriptor,
        offset: float,
        label: str = None,
        tolerance: Optional[Union[float, Tuple[float, float]]] = None,
    ):
        """ Create a dimension line with two lines extending outward from the part to dimension """

        # Create a wire modelling the path of the dimension lines from a variety of input types
        object_path = Draft.path_to_wire(object_edge)
        object_length = object_path.Length()

        extension_tangent = object_path.tangentAt(0).cross(self._label_normal)
        dimension_plane = cq.Plane(
            origin=object_path.positionAt(0),
            xDir=extension_tangent,
            normal=self._label_normal,
        )
        ext_line0 = (
            cq.Workplane(dimension_plane).moveTo(1.5 * MM, 0).lineTo(offset + 3 * MM, 0)
        )
        ext_line1 = (
            cq.Workplane(dimension_plane)
            .moveTo(1.5 * MM, object_length)
            .lineTo(offset + 3 * MM, object_length)
        )

        p0 = ext_line0.val().positionAt(
            offset / (offset + (offset / abs(offset)) * 3 * MM)
        )
        p1 = ext_line1.val().positionAt(
            offset / (offset + (offset / abs(offset)) * 3 * MM)
        )
        e_line = cq.Assembly(None, name="extension_line", color=self.color)
        e_line.add(ext_line0, name="extension_line0")
        e_line.add(ext_line1, name="extension_line1")

        e_line.add(
            self.dimension_line(label=label, path=[p0, p1], tolerance=tolerance),
            name="dimension_line",
        )
        return e_line

    @validate_arguments(config=dict(arbitrary_types_allowed=True))
    def callout(
        self,
        label: str,
        tail: Optional[PathDescriptor] = None,
        origin: Optional[PointDescriptor] = None,
        justify: Literal["left", "center", "right"] = "left",
    ):
        """ Create a text box that optionally points at something """

        if origin is not None:
            text_origin = (
                cq.Vector(origin)
                if isinstance(origin, (cq.Vector, tuple))
                else cq.Vector(origin.toTuple())
            )
        elif tail is not None:
            line_wire = Draft.path_to_wire(tail)
            line_length = line_wire.Length()
            text_origin = line_wire.positionAt(0)
        else:
            raise ValueError("Either origin or tail must be provided")

        text_plane = cq.Plane(
            origin=text_origin, xDir=self._label_x_dir, normal=self._label_normal
        )
        t_box = cq.Assembly(None, name=label + "_callout", color=self.color)
        label_text = cq.Workplane(text_plane).text(
            txt=label,
            fontsize=self.font_size,
            distance=self.font_size / 100,
            halign=justify,
        )
        t_box.add(label_text, name="callout_label")
        if tail is not None:
            t_box.add(
                Draft.line_segment(
                    line_wire, tip_pos=1.5 * MM / line_length, tail_pos=1.0
                ),
                name="callout_line",
            )
            t_box.add(
                self.arrow_and_shaft(line_wire, tip_pos="end"), name="callout_arrow",
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
