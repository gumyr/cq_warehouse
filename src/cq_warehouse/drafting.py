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
from math import floor, log2, gcd, pi, copysign
from typing import Union, Tuple, Literal, Optional, ClassVar, List
from cadquery import (
    Wire,
    Edge,
    Vector,
    Vertex,
    Color,
    Assembly,
    Solid,
    Workplane,
    Plane,
)
from cadquery.occ_impl.shapes import VectorLike
import cq_warehouse.extensions

MM = 1
INCH = 25.4 * MM

PathDescriptor = Union[
    Wire,
    Edge,
    List[Union[Vector, Vertex, Tuple[float, float, float]]],
]
PointDescriptor = Union[Vector, Vertex, Tuple[float, float, float]]


class Draft:
    """Draft

    Documenting cadquery designs with dimension and extension lines as well as callouts.


    Args:
        font_size (float): size of the text in dimension lines and callouts. Defaults to 5.0.
        color (Color, optional): color of text, extension lines and arrows. Defaults to Color(0.25, 0.25, 0.25).
        arrow_diameter (float): maximum diameter of arrow heads. Defaults to 1.0.
        arrow_length (float): arrow head length. Defaults to 3.0.
        label_normal (VectorLike, optional): text and extension line plane normal. Defaults to XY plane.
        units (Literal["metric", "imperial"]): unit of measurement. Defaults to "metric".
        number_display (Literal["decimal", "fraction"]): display numbers as decimals or fractions. Defaults to "decimal".
        display_units (bool): control the display of units with numbers. Defaults to True.
        decimal_precision (int): number of decimal places when displaying numbers. Defaults to 2.
        fractional_precision (int): maximum fraction denominator - must be a factor of 2. Defaults to 64.
        extension_gap (float): gap between the point and start of extension line in extension_line.

    Example:

        .. code-block:: python

            metric_drawing = Draft(decimal_precision=1)
            length_dimension_line = metric_drawing.extension_line(
                object_edge=mystery_object.faces("<Z").vertices("<Y").vals(),
                offset=10.0,
                tolerance=(+0.2, -0.1),
            )

    The three public methods that the Draft class defines are described below. Note that both
    dimension_line ane extension_line support arcs as well as linear measurements - to be exact, the
    shown measurement is the length of the input path or object edge which could be an arbitrary shape
    like a spline. If this path or object_edge is part of a circle the size of the arc in degrees may
    be displayed instead of the length.

    """

    # Class Attributes
    unit_LUT: ClassVar[dict] = {"metric": "mm", "imperial": '"'}

    # Override the __init__ method to set a default color as
    # >>> color: Color = Color(0.25,0.25,0.25)
    # results in
    # >>> TypeError: cannot pickle 'OCP.Quantity.Quantity_ColorRGBA' object
    def __init__(
        self,
        font_size: float = 5.0,
        color: Optional[Color] = Color(0.25, 0.25, 0.25),
        arrow_diameter: float = 1.0,
        arrow_length: float = 3.0,
        label_normal: Optional[VectorLike] = None,
        units: Literal["metric", "imperial"] = "metric",
        number_display: Literal["decimal", "fraction"] = "decimal",
        display_units: bool = True,
        decimal_precision: int = 2,
        fractional_precision: int = 64,
        extension_gap: float = 0,
    ):
        self.font_size = font_size
        self.color = color
        self.arrow_diameter = arrow_diameter
        self.arrow_length = arrow_length
        self.label_normal = label_normal
        self.units = units
        self.number_display = number_display
        self.display_units = display_units
        self.decimal_precision = decimal_precision
        self.fractional_precision = fractional_precision
        self.extension_gap = extension_gap

        if not log2(fractional_precision).is_integer():
            raise ValueError(
                f"fractional_precision values must be a factor of 2; provided {fractional_precision}"
            )
        if units not in ["metric", "imperial"]:
            raise ValueError(f"units must be one of 'metric' or 'imperial' not {units}")
        if number_display not in ["decimal", "fraction"]:
            raise ValueError(
                f"number_display must be one of 'decimal' or 'fraction' not {number_display}"
            )
        self._label_normal = (
            Vector(0, 0, 1)
            if self.label_normal is None
            else Vector(self.label_normal).normalized()
        )
        self._label_x_dir = (
            Vector(0, 1, 0)
            if self._label_normal == Vector(1, 0, 0)
            else Vector(1, 0, 0)
        )
        # self.color = Color(0.25, 0.25, 0.25) if self.color is None else self.color

    def round_to_str(self, number: float) -> str:
        """Round a float but remove decimal if appropriate and convert to str"""
        return (
            f"{round(number, self.decimal_precision):.{self.decimal_precision}f}"
            if self.decimal_precision > 0
            else str(int(round(number, self.decimal_precision)))
        )

    def _number_with_units(
        self,
        number: float,
        tolerance: Union[float, Tuple[float, float]] = None,
        display_units: Optional[bool] = None,
    ) -> str:
        """Convert a raw number to a unit of measurement string based on the class settings"""

        def simplify_fraction(numerator: int, denominator: int) -> Tuple[int, int]:
            """Mathematically simplify a fraction given a numerator and demoninator"""
            greatest_common_demoninator = gcd(numerator, denominator)
            return (
                int(numerator / greatest_common_demoninator),
                int(denominator / greatest_common_demoninator),
            )

        if display_units is None:
            if tolerance is None:
                qualified_display_units = self.display_units
            else:
                qualified_display_units = False
        else:
            qualified_display_units = display_units

        unit_str = Draft.unit_LUT[self.units] if qualified_display_units else ""
        if tolerance is None:
            tolerance_str = ""
        elif isinstance(tolerance, float):
            tolerance_str = f" ±{self._number_with_units(tolerance)}"
        else:
            tolerance_str = f" +{self._number_with_units(tolerance[0],display_units=False)} -{self._number_with_units(tolerance[1])}"

        if self.units == "metric" or self.number_display == "decimal":
            unit_lut = {"metric": MM, "imperial": INCH}
            measurement = self.round_to_str(number / unit_lut[self.units])
            return_value = f"{measurement}{unit_str}{tolerance_str}"
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

    def _make_arrow(
        self, path: Union[Edge, Wire], tip_pos: Literal["start", "end"] = "start"
    ) -> Solid:
        """Create an arrow head which follows the provided path"""

        path_as_wire = path if isinstance(path, Wire) else Wire.assembleEdges([path])
        # Calculate the position along the path to create the arrow cross-sections
        loft_pos = [0.0 if tip_pos == "start" else 1.0]
        for i in [2, 1]:
            loft_pos.append(
                self.arrow_length / (i * path_as_wire.Length())
                if tip_pos == "start"
                else 1.0 - self.arrow_length / (i * path_as_wire.Length())
            )
        radius_lut = {0: 0.0001, 1: 0.2, 2: 0.5}
        arrow_cross_sections = [
            Wire.assembleEdges(
                [
                    Edge.makeCircle(
                        radius=radius_lut[i] * self.arrow_diameter,
                        pnt=path.positionAt(loft_pos[i]),
                        dir=path.tangentAt(loft_pos[i]),
                    )
                ]
            )
            for i in range(3)
        ]
        arrow = Assembly(None, name="arrow")
        arrow.add(
            Solid.makeLoft(arrow_cross_sections),
            name="arrow_and_shaft",
        )
        arrow.add(path, name="arrow_shaft")
        return arrow

    @staticmethod
    def _segment_line(path: Union[Edge, Wire], tip_pos: float, tail_pos: float) -> Edge:
        """Create a segment of a path between tip and tail (inclusive)"""

        if not 0.0 <= tip_pos <= 1.0:
            raise ValueError(f"tip_pos value of {tip_pos} is not between 0.0 and 1.0")
        if not 0.0 <= tail_pos <= 1.0:
            raise ValueError(f"tail_pos value of {tail_pos} is not between 0.0 and 1.0")

        sub_path = Edge.makeSpline(
            listOfVector=[
                path.positionAt(tip_pos + i * (tail_pos - tip_pos) / 16)
                for i in range(17)
            ],
            tangents=[path.tangentAt(t) for t in [tip_pos, tail_pos]],
        )
        return sub_path

    @staticmethod
    def _project_wire(path: Wire, line: VectorLike) -> Wire:
        """Project a Wire to a line."""
        if isinstance(line, Tuple):
            line = Vector(line)
        path_as_wire = Wire.assembleEdges(
            Workplane()
            .polyline(
                [
                    path.startPoint().projectToLine(line),
                    path.endPoint().projectToLine(line)
                ]
            )
            .vals()
        )
        return path_as_wire

    @staticmethod
    def _path_to_wire(path: PathDescriptor) -> Wire:
        """Convert a PathDescriptor into a Wire"""
        if isinstance(path, Wire):
            path_as_wire = path
        elif isinstance(path, Edge):
            path_as_wire = Wire.assembleEdges([path])
        else:
            path_as_wire = Wire.assembleEdges(
                Workplane()
                .polyline(
                    [
                        Vector(p.toTuple()) if isinstance(p, Vertex) else Vector(p)
                        for p in path
                    ]
                )
                .vals()
            )
        return path_as_wire

    def _label_size(self, label_str: str) -> float:
        """Return the length of a text string given class parameters"""
        label_xy_object = Workplane("XY").text(
            txt=label_str,
            fontsize=self.font_size,
            distance=self.font_size / 20,
            # font=self.font_name,
            # kind = self.font_style,
        )
        label_length = 2.25 * max([v.X for v in label_xy_object.vertices().vals()])
        return label_length

    @staticmethod
    def _find_center_of_arc(arc: Edge) -> Vector:
        """Given an arc find the center of the circle"""
        arc_radius = arc.radius()
        arc_pnt = arc.positionAt(0.25)
        chord_end_points = [arc.positionAt(t) for t in [0.0, 0.5]]
        chord_line = Edge.makeLine(*chord_end_points)
        chord_center_pnt = chord_line.positionAt(0.5)
        radial_tangent = Edge.makeLine(arc_pnt, chord_center_pnt).tangentAt(0)
        center = arc_pnt + radial_tangent * arc_radius
        return center

    def _label_to_str(
        self,
        label: str,
        line_wire: Wire,
        label_angle: bool,
        tolerance: Optional[Union[float, Tuple[float, float]]],
    ) -> str:
        """Create the str to use as the label text"""
        line_length = line_wire.Length()
        if label is not None:
            label_str = label
        elif label_angle:
            arc_edge = Workplane(line_wire).edges("%circle").val()
            try:
                arc_radius = arc_edge.radius()
            except AttributeError as not_an_arc_error:
                raise ValueError(
                    "label_angle requested but the path is not part of a circle"
                ) from not_an_arc_error
            arc_size = 360 * line_length / (2 * pi * arc_radius)
            label_str = f"{self.round_to_str(arc_size)}°"
        else:
            label_str = self._number_with_units(line_length, tolerance)
        return label_str

    def _make_arrow_shaft(
        self,
        label_length: float,
        line_wire: Wire,
        internal: bool,
        arrow_pos: Literal["start", "end"],
    ) -> Edge:
        line_length = line_wire.Length()

        # Calculate the relative positions along the dimension_line line of the key features
        if arrow_pos == "start":
            line_controls = [
                0.0,
                0.5 - (label_length / 2) / line_length,
            ]
            line_wire_pos = 0.0
            start_pnt = (0, 0)
            end_pnt = -1.5 * self.font_size

        else:
            line_controls = [
                0.5 + (label_length / 2) / line_length,
                1.0,
            ]
            line_wire_pos = 1.0
            start_pnt = (1.5 * self.font_size, 0)
            end_pnt = 0

        if internal:
            arrow_shaft = Draft._segment_line(
                line_wire, tip_pos=line_controls[0], tail_pos=line_controls[1]
            )
        else:
            arrow_shaft = (
                Workplane(
                    Plane(
                        # origin=line_wire.positionAt(line_wire_pos),
                        line_wire.positionAt(line_wire_pos),
                        xDir=line_wire.tangentAt(line_wire_pos),
                        normal=self._label_normal,
                    )
                )
                .moveTo(*start_pnt)
                .hLineTo(end_pnt)
                .val()
            )

        return arrow_shaft

    def _str_to_object(
        self,
        position: Literal["start", "center", "end"],
        label_str: str,
        location_wire: Wire,
    ) -> Solid:
        if position == "center":
            text_plane = Plane(
                # origin=location_wire.positionAt(0.5),
                location_wire.positionAt(0.5),
                xDir=location_wire.tangentAt(0.5),
                normal=self._label_normal,
            )
            label_object = Workplane(text_plane).text(
                # txt=label_str, fontsize=self.font_size, distance=self.font_size / 100
                label_str,
                fontsize=self.font_size,
                distance=self.font_size / 100,
            )
        elif position == "end":
            text_plane = Plane(
                origin=location_wire.tangentAt(0.0) * -1.5 * MM
                + location_wire.positionAt(0.0),
                xDir=location_wire.tangentAt(0.0) * -1,
                normal=self._label_normal,
            )
            label_object = Workplane(text_plane).text(
                # txt=label_str,
                label_str,
                fontsize=self.font_size,
                distance=self.font_size / 100,
                halign="left",
            )
        else:  # position=="start"
            text_plane = Plane(
                # origin=location_wire.tangentAt(1.0) * 1.5 * MM
                # + location_wire.positionAt(1.0),
                location_wire.tangentAt(1.0) * 1.5 * MM + location_wire.positionAt(1.0),
                xDir=location_wire.tangentAt(1.0) * -1,
                normal=self._label_normal,
            )
            label_object = Workplane(text_plane).text(
                # txt=label_str,
                label_str,
                fontsize=self.font_size,
                distance=self.font_size / 100,
                halign="right",
            )
        return label_object

    def dimension_line(
        self,
        path: PathDescriptor,
        label: Optional[str] = None,
        arrows: Tuple[bool, bool] = (True, True),
        tolerance: Optional[Union[float, Tuple[float, float]]] = None,
        label_angle: bool = False,
    ) -> Assembly:
        """Dimension Line

        Create a dimension line typically for internal measurements.
        Typically used for (but not restricted to) inside dimensions, a dimension line often
        as arrows on either side of a dimension or label.

        There are three options depending on the size of the text and length
        of the dimension line:
        Type 1) The label and arrows fit within the length of the path
        Type 2) The text fit within the path and the arrows go outside
        Type 3) Neither the text nor the arrows fit within the path

        Args:
            path (PathDescriptor): a very general type of input used to describe the path the
                dimension line will follow .
            label (Optional[str], optional): a text string which will replace the length (or
                arc length) that would otherwise be extracted from the provided path. Providing
                a label is useful when illustrating a parameterized input where the name of an
                argument is desired not an actual measurement. Defaults to None.
            arrows (Tuple[bool, bool], optional): a pair of boolean values controlling the placement
                of the start and end arrows. Defaults to (True, True).
            tolerance (Optional[Union[float, Tuple[float, float]]], optional): an optional tolerance
                value to add to the extracted length value. If a single tolerance value is provided
                it is shown as ± the provided value while a pair of values are shown as
                separate + and - values. Defaults to None.
            label_angle (bool, optional): a flag indicating that instead of an extracted length value,
                the size of the circular arc extracted from the path should be displayed in degrees.

        Raises:
            ValueError: No output - insufficient space for labels and no arrows selected

        Returns:
            Assembly: the dimension line
        """

        # Create a wire modelling the path of the dimension lines from a variety of input types
        line_wire = Draft._path_to_wire(path)
        line_length = line_wire.Length()

        label_str = self._label_to_str(label, line_wire, label_angle, tolerance)
        label_length = self._label_size(label_str)

        # Determine the type of this dimension line
        if label_length + arrows.count(True) * self.arrow_length < line_length:
            dline_type = 1
        elif label_length < line_length:
            dline_type = 2
        else:
            dline_type = 3

        if dline_type == 3 and arrows.count(True) == 0:
            raise ValueError(
                "No output - insufficient space for labels and no arrows selected"
            )

        # Compose an assembly with the component parts of the dimension_line line
        d_line = Assembly(None, name=label_str + "_dimension_line", color=self.color)

        # For the start and end arrow generate complete arrows from shafts and the label object
        for i, arrow_pos in enumerate(["start", "end"]):
            if arrows[i]:
                arrow_shaft = self._make_arrow_shaft(
                    label_length, line_wire, dline_type == 1, arrow_pos
                )
                d_line.add(
                    self._make_arrow(arrow_shaft, tip_pos=arrow_pos),
                    name=arrow_pos + "_arrow",
                )
                label_object = self._str_to_object(arrow_pos, label_str, arrow_shaft)

        # If the label is located along the input path generate a central label
        if dline_type in [1, 2]:
            label_object = self._str_to_object("center", label_str, line_wire)

        # Finish off the assembly
        d_line.add(label_object, name="label")

        return d_line

    def extension_line(
        self,
        object_edge: PathDescriptor,
        offset: float,
        label: str = None,
        arrows: Tuple[bool, bool] = (True, True),
        tolerance: Optional[Union[float, Tuple[float, float]]] = None,
        label_angle: bool = False,
        project_line: Optional[VectorLike] = None,
    ) -> Assembly:
        """Extension Line

        Create a dimension line with two lines extending outward from the part to dimension.
        Typically used for (but not restricted to) outside dimensions, with a pair of lines
        extending from the edge of a part to a dimension line.

        Args:
            object_edge (PathDescriptor): a very general type of input defining the object to
                be dimensioned. Typically this value would be extracted from the part but is
                not restricted to this use.
            offset (float): a distance to displace the dimension line from the edge of the object
            label (str, optional): a text string which will replace the length (or arc length)
                that would otherwise be extracted from the provided path. Providing a label is
                useful when illustrating a parameterized input where the name of an argument
                is desired not an actual measurement. Defaults to None.
            arrows (Tuple[bool, bool], optional): a pair of boolean values controlling the placement
                of the start and end arrows. Defaults to (True, True).
            tolerance (Optional[Union[float, Tuple[float, float]]], optional): an optional tolerance
                value to add to the extracted length value. If a single tolerance value is provided
                it is shown as ± the provided value while a pair of values are shown as
                separate + and - values. Defaults to None.
            label_angle (bool, optional): a flag indicating that instead of an extracted length
                value, the size of the circular arc extracted from the path should be displayed
                in degrees. Defaults to False.
            project_line (Vector, optional): Vector line which to project dimension against.

        Returns:
            Assembly: the extension line
        """

        # Create a wire modelling the path of the dimension lines from a variety of input types
        object_path = Draft._path_to_wire(object_edge)
        object_start = object_path.startPoint()
        object_end = object_path.endPoint()
        if project_line:
            object_path = Draft._project_wire(object_path, project_line)
        object_length = object_path.Length()

        # Determine if the provided object edge is a circular arc and if so extract its radius
        arc_edge = Workplane(object_path).edges("%circle").val()
        try:
            arc_radius = arc_edge.radius()
        except AttributeError:
            is_arc = False
        else:
            is_arc = True

        if is_arc:
            # Create a new arc for the dimension line offset from the given one
            arc_center = Draft._find_center_of_arc(arc_edge)
            radial_directions = [
                Edge.makeLine(arc_center, object_path.positionAt(i)).tangentAt(1.0)
                for i in [0.0, 0.5, 1.0]
            ]
            offset_arc_pts = [
                arc_center + radial_directions[i] * (arc_radius + offset)
                for i in range(3)
            ]
            extension_path = Edge.makeThreePointArc(*offset_arc_pts)
            # Create radial extension lines
            ext_line = [
                Edge.makeLine(
                    object_path.positionAt(i)
                    + radial_directions[i * 2] * copysign(1, offset) * 1.5 * MM,
                    object_path.positionAt(i)
                    + radial_directions[i * 2]
                    * (offset + copysign(1, offset) * 3.0 * MM),
                )
                for i in range(2)
            ]
        else:
            extension_tangent = object_path.tangentAt(0).cross(self._label_normal)
            dimension_plane = Plane(
                object_path.positionAt(0),
                xDir=extension_tangent,
                normal=self._label_normal,
            )
            start_point = dimension_plane.toLocalCoords(object_start).toTuple()[:2]
            end_point = dimension_plane.toLocalCoords(object_end).toTuple()[:2]
            extension_gap = copysign(1, offset) * self.extension_gap * MM
            ext_line1 = (
                Workplane(dimension_plane)
                .moveTo(start_point[0] + extension_gap, start_point[1])
                .lineTo(offset + extension_gap, start_point[1])
            )
            ext_line2 = (
                Workplane(dimension_plane)
                .moveTo(end_point[0] + extension_gap, end_point[1])
                .lineTo(offset + extension_gap, end_point[1])
            )
            ext_line = [ext_line1, ext_line2]
            extension_path = object_path.translate(
                extension_tangent.normalized() * offset
            )

        # Create the assembly
        d_line = self.dimension_line(
            label=label,
            path=extension_path,
            arrows=arrows,
            tolerance=tolerance,
            label_angle=label_angle,
        )
        e_line = Assembly(
            None, name=d_line.name.replace("dimension", "extension"), color=self.color
        )
        e_line.add(ext_line[0], name="extension_line0")
        e_line.add(ext_line[1], name="extension_line1")
        e_line.add(d_line, name="dimension_line")
        return e_line

    def callout(
        self,
        label: str,
        tail: Optional[PathDescriptor] = None,
        origin: Optional[PointDescriptor] = None,
        justify: Literal["left", "center", "right"] = "left",
    ) -> Assembly:
        """Callout

        A text box with or without a tail pointing to another object used to provide
        extra information to the reader.

        Args:
            label (str): the text to place within the callout - note that including a ``\\n``
                in the text string will split the text over multiple lines.
            tail (Optional[PathDescriptor], optional): an optional tail defined as above -
                note that if provided the text origin will be the start of the tail.
                Defaults to None.
            origin (Optional[PointDescriptor], optional): a very general definition of anchor
                point of the text defined as
                ``PointDescriptor = Union[Vector, Vertex, Tuple[float, float, float]]``
                Defaults to None.
            justify (Literal[, optional): text alignment. Defaults to "left".

        Raises:
            ValueError: Either origin or tail must be provided

        Returns:
            Assembly: the callout

        """

        if origin is not None:
            text_origin = (
                Vector(origin)
                if isinstance(origin, (Vector, tuple))
                else Vector(origin.toTuple())
            )
        elif tail is not None:
            line_wire = Draft._path_to_wire(tail)
            text_origin = line_wire.positionAt(0)
        else:
            raise ValueError("Either origin or tail must be provided")

        text_plane = Plane(
            # origin=text_origin, xDir=self._label_x_dir, normal=self._label_normal
            text_origin,
            xDir=self._label_x_dir,
            normal=self._label_normal,
        )
        t_box = Assembly(None, name=label + "_callout", color=self.color)
        label_text = Workplane(text_plane).text(
            # txt=label,
            label,
            fontsize=self.font_size,
            distance=self.font_size / 100,
            halign=justify,
            # font=self.font_name,
            # kind = self.font_style,
        )
        t_box.add(label_text, name="callout_label")
        if tail is not None:
            t_box.add(
                self._make_arrow(line_wire, tip_pos="end"),
                name="callout_tail",
            )

        return t_box
