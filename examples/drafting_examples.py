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

VectorLike = Union[Tuple[float, float], Tuple[float, float, float], cq.Vector]


class Draft:
    """
    Create 3D engineering dimension_line lines for documenting cadquery designs

    The class stores the style descriptor for the methods

    Methods
    -------
    dimension_line - 2 points
    dimension_line - path
    angular_dimension_line
    label - target point, label point

    """

    def __init__(
        self,
        font_size: float = 5.0,
        color: cq.Color = None,
        arrow_diameter: float = None,
        arrow_length: float = None,
        label_normal: VectorLike = None,
        units: Literal["metric", "imperial"] = "metric",
        unit_display: Literal["decimal", "fraction"] = "decimal",
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
        if unit_display in ["decimal", "fraction"]:
            self.unit_display = unit_display
        else:
            raise ValueError(f'units must be one of {"decimal", "fraction"}')
        self.decimal_precision = decimal_precision
        if log2(fractional_precision).is_integer():
            self.fractional_precision = fractional_precision
        else:
            raise ValueError(
                f"fractional_precision values must be a factor of 2, {fractional_precision} provided"
            )

    def number_with_units(self, number: float) -> str:
        """ Convert a raw number to a unit of measurement string based on the class settings """

        def simplify_fraction(numerator: int, denominator: int) -> tuple[int, int]:
            greatest_common_demoninator = gcd(numerator, denominator)
            return (
                int(numerator / greatest_common_demoninator),
                int(denominator / greatest_common_demoninator),
            )

        if self.units == "metric":
            return_value = f"{number / MM:.{self.decimal_precision}f}mm"
        elif self.unit_display == "decimal":
            return_value = f'{number / INCH:.{self.decimal_precision}f}"'
        else:
            whole_part = floor(number / INCH)
            (numerator, demoninator) = simplify_fraction(
                round((number / INCH - whole_part) * self.fractional_precision),
                self.fractional_precision,
            )
            if whole_part == 0:
                return_value = f'{numerator}/{demoninator}"'
            else:
                return_value = f'{whole_part} {numerator}/{demoninator}"'

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
        path: tuple[VectorLike, VectorLike],
        label: str = None,
        arrow_heads: tuple[bool, bool] = None,
    ) -> cq.Workplane:
        ...

    @overload
    def dimension_line(
        self,
        path: Union[cq.Wire, cq.Edge],
        label: str = None,
        arrow_heads: tuple[bool, bool] = None,
    ) -> cq.Workplane:
        ...

    @overload
    def dimension_line(
        self,
        path: list[cq.Vertex],
        label: str = None,
        arrow_heads: tuple[bool, bool] = None,
    ) -> cq.Workplane:
        ...

    def dimension_line(self, path, label=None, arrow_heads=None,) -> cq.Workplane:
        """ Create a 3D engineering dimension_line line for documenting CAD designs """

        # Parse arguments
        if isinstance(path, (cq.Edge, cq.Wire)):
            line_path = cq.Wire.assembleEdges([path])
        elif all(isinstance(point, (cq.Vector, tuple)) for point in path):
            line_path = cq.Wire.assembleEdges(
                [cq.Edge.makeLine(cq.Vector(path[0]), cq.Vector(path[1]))]
            )
        elif all(isinstance(point, cq.Vertex) for point in path) and len(path) == 2:
            line_path = cq.Wire.assembleEdges(
                [
                    cq.Edge.makeLine(
                        cq.Vector(path[0].toTuple()), cq.Vector(path[1].toTuple())
                    )
                ]
            )
        else:
            raise TypeError(
                "path must be a tuple of vector, list of vertex, cq.Edge or cq.Wire"
            )
        arrows = [True, True] if arrow_heads is None else arrow_heads
        line_length = line_path.Length()
        label_str = self.number_with_units(line_length) if label is None else label

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
            txt=label_str, fontsize=self.font_size, distance=self.font_size / 20
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
        self, label: str, object_edge: tuple[VectorLike, VectorLike], offset: float
    ):
        ...

    @overload
    def extension_line(
        self, label: str, object_edge: Union[cq.Wire, cq.Edge], offset: float
    ):
        ...

    @overload
    def extension_line(
        self, label: str, object_edge: list[cq.Vertex], offset: float,
    ):
        ...

    def extension_line(self, label: str, object_edge, offset: float):
        """ Create a dimension line with two lines extending outward from the part to dimension """
        # Parse arguments
        if isinstance(object_edge, (cq.Edge, cq.Wire)):
            object_path = cq.Wire.assembleEdges([object_edge])
        elif all(isinstance(point, (cq.Vector, tuple)) for point in object_edge):
            object_path = cq.Wire.assembleEdges(
                [cq.Edge.makeLine(cq.Vector(object_edge[0]), cq.Vector(object_edge[1]))]
            )
        elif (
            all(isinstance(point, cq.Vertex) for point in object_edge)
            and len(object_edge) == 2
        ):
            object_path = cq.Wire.assembleEdges(
                [
                    cq.Edge.makeLine(
                        cq.Vector(object_edge[0].toTuple()),
                        cq.Vector(object_edge[1].toTuple()),
                    )
                ]
            )
        else:
            raise ValueError(
                "object_edge must be a tuple of vector, list of vertex, cq.Edge or cq.Wire"
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
            .moveTo(1.5 * MM, -object_length)
            .lineTo(offset + 3 * MM, -object_length)
        )

        p0 = ext_line0.val().positionAt(offset / (offset + 3 * MM))
        p1 = ext_line1.val().positionAt(offset / (offset + 3 * MM))
        e_line = cq.Assembly(None, name=label + "_extension_line", color=self.color)
        e_line.add(ext_line0, name="extension_line0")
        e_line.add(ext_line1, name="extension_line1")
        e_line.add(
            self.dimension_line(label=label, path=(p0, p1)), name="dimension_line",
        )
        return e_line

    def text_box(
        self,
        label: str,
        location: VectorLike,
        point_at: VectorLike = None,
        justify: Literal["left", "right"] = "left",
    ):
        """ Create a text box that optionally points at something """
        text_plane = cq.Plane(
            origin=cq.Vector(location), xDir=cq.Vector(1, 0, 0), normal=self.label_norm,
        )
        t_box = cq.Assembly(None, name=label + "_text_box", color=self.color)
        label_text = cq.Workplane(text_plane).text(
            txt=label,
            fontsize=self.font_size,
            distance=self.font_size / 20,
            halign=justify,
        )
        t_box.add(label_text, name="text_box_label")
        if point_at is not None:
            line_path = cq.Wire.assembleEdges(
                [cq.Edge.makeLine(cq.Vector(location), cq.Vector(point_at))]
            )
            line_length = line_path.Length()
            t_box.add(
                Draft.line_segment(
                    line_path, tip_pos=1.5 * MM / line_length, tail_pos=1.0
                ),
                name="text_box_line",
            )
            t_box.add(
                self.arrow_head(
                    line_path,
                    tip_pos=1.0,
                    tail_pos=1.0 - self.arrow_length / line_length,
                ),
                name="text_box_arrow",
            )

        return t_box


if __name__ == "__main__" or "show_object" in locals():
    metric_drawing = Draft(decimal_precision=2)
    print(metric_drawing.number_with_units(3.141))
    print(metric_drawing.number_with_units(3.149))
    print(metric_drawing.number_with_units(0))
    imperial_drawing = Draft(units="imperial")
    print(imperial_drawing.number_with_units((5 / 8) * INCH))
    imperial_fractional_drawing = Draft(units="imperial", unit_display="fraction")
    print(imperial_fractional_drawing.number_with_units((5 / 8) * INCH))
    print(imperial_fractional_drawing.number_with_units(pi * INCH))
    draft_obj = Draft(font_size=5, color=cq.Color(0.75, 0.25, 0.25))
    draft_obj_y = Draft(
        font_size=8, color=cq.Color(0.75, 0.25, 0.25), label_normal=cq.Vector(0, -1, 0),
    )
    test0 = draft_obj.dimension_line(
        path=((0, 0, 0), (40 * cos(pi / 6), -40 * sin(pi / 6), 0))
    )
    test1 = imperial_fractional_drawing.dimension_line(path=((-40, 0, 0), (40, 0, 0)))
    test2 = draft_obj_y.dimension_line(
        label="test2",
        path=cq.Edge.makeThreePointArc(
            cq.Vector(-40, 0, 0),
            cq.Vector(-40 * sqrt(2) / 2, 0, 40 * sqrt(2) / 2),
            cq.Vector(0, 0, 40),
        ),
    )
    test3 = draft_obj_y.dimension_line(
        label="test3",
        path=cq.Edge.makeThreePointArc(
            cq.Vector(0, 0, 40),
            cq.Vector(40 * sqrt(2) / 2, 0, 40 * sqrt(2) / 2),
            cq.Vector(40, 0, 0),
        ),
    )
    test4 = draft_obj.dimension_line(
        label="test4",
        path=cq.Edge.makeThreePointArc(
            cq.Vector(-40, 0, 0), cq.Vector(0, -40, 0), cq.Vector(40, 0, 0)
        ),
    )
    draft_obj_oblique = Draft(
        font_size=8,
        color=cq.Color(0.75, 0.25, 0.25),
        label_normal=cq.Vector(0, -0.5, 1),
    )
    test5 = draft_obj_oblique.dimension_line(
        label="test5",
        path=cq.Edge.makeSpline(
            [cq.Vector(-40, 0, 0), cq.Vector(35, 20, 10), cq.Vector(40, 0, 0)]
        ),
    )
    test6 = draft_obj.dimension_line(
        label="test6", arrow_heads=[False, True], path=(cq.Vector(40, 0, 0), (80, 0, 0))
    )
    test7 = draft_obj.dimension_line(
        label="test7",
        arrow_heads=[True, False],
        path=((-80, 0, 0), cq.Vector(-40, 0, 0)),
    )
    test8 = draft_obj.dimension_line(
        label="test8",
        arrow_heads=[True, False],
        path=(cq.Vertex.makeVertex(0, -80, 0), cq.Vertex.makeVertex(0, -40, 0)),
    )
    test9 = draft_obj.extension_line(
        label="test9",
        object_edge=(cq.Vertex.makeVertex(0, -80, 0), cq.Vertex.makeVertex(0, -40, 0)),
        offset=10 * MM,
    )
    test10 = draft_obj.extension_line(
        label="80mm", object_edge=((-40, 0, 0), (40, 0, 0)), offset=30 * MM,
    )
    test11 = draft_obj.text_box(label="two\nlines", location=(40, 40, 0))
    test12 = draft_obj.text_box(
        label="look\nhere", location=(40, -40, 0), point_at=(0, -40, 0)
    )
    # with cProfile.Profile() as pr:
    #     test3 = dimension_line("test3",
    #         path=cq.Edge.makeThreePointArc(
    #             cq.Vector(0,0,40),
    #             cq.Vector(40*sqrt(2)/2,0,40*sqrt(2)/2),
    #             cq.Vector(40,0,0)
    #         )
    #     )
    # stats = pstats.Stats(pr)
    # stats.sort_stats(pstats.SortKey.TIME)
    # stats.print_stats()


# If running from within the cq-editor, show the dimension_line lines
if "show_object" in locals():
    show_object(test0, name="test0")
    show_object(test1, name="test1")
    show_object(test2, name="test2")
    show_object(test3, name="test3")
    show_object(test4, name="test4")
    show_object(test5, name="test5")
    show_object(test6, name="test6")
    show_object(test7, name="test7")
    show_object(test8, name="test8")
    show_object(test9, name="test9")
    show_object(test10, name="test10")
    show_object(test11, name="test11")
    show_object(test12, name="test12")
