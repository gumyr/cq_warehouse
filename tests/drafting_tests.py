"""

Drafting Unit Tests

name: drafting_tests.py
by:   Gumyr
date: July 14th 2021

desc: Unit tests for the drafting sub-package of cq_warehouse

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
import math
import unittest
from tests import BaseTest
import cadquery as cq
from cq_warehouse.drafting import Draft

MM = 1
INCH = 25.4 * MM


class TestParsing(BaseTest):
    # def test_dimension_line(self):
    #     def test_extension_line(self):
    #     def test_text_box(self):
    def test_draft_instantiation(self):
        with self.assertRaises(ValueError):
            Draft(units="normal")
        with self.assertRaises(ValueError):
            Draft(number_display="normal")
        with self.assertRaises(ValueError):
            Draft(fractional_precision=37)
        line_edge = cq.Edge.makeLine(cq.Vector(0, 0, 0), cq.Vector(0, 0, 1))
        line_wire = cq.Wire.assembleEdges([line_edge])
        with self.assertRaises(ValueError):
            Draft.line_segment(path=line_edge, tip_pos=-1.0, tail_pos=1.0)
        with self.assertRaises(ValueError):
            Draft.line_segment(path=line_wire, tip_pos=2.0, tail_pos=1.0)
        with self.assertRaises(ValueError):
            Draft.line_segment(path=line_edge, tip_pos=0.0, tail_pos=-1.0)
        with self.assertRaises(ValueError):
            Draft.line_segment(path=line_edge, tip_pos=0.0, tail_pos=2.0)
        with self.assertRaises(TypeError):
            Draft.line_segment(path="line", tip_pos=0.0, tail_pos=1.0)

    def test_draft_instantiation(self):
        default_draft = Draft()
        with self.assertRaises(ValueError):
            default_draft.text_box(label="test", location=(0, 0, 0), justify="centre")


class TestFunctionality(BaseTest):
    def test_number_with_units(self):
        metric_drawing = Draft(decimal_precision=2)
        self.assertEqual(metric_drawing.number_with_units(3.141), "3.14mm")
        self.assertEqual(metric_drawing.number_with_units(3.149), "3.15mm")
        self.assertEqual(metric_drawing.number_with_units(0), "0.00mm")
        imperial_drawing = Draft(units="imperial")
        self.assertEqual(imperial_drawing.number_with_units((5 / 8) * INCH), '0.62"')
        imperial_fractional_drawing = Draft(units="imperial", number_display="fraction")
        self.assertEqual(
            imperial_fractional_drawing.number_with_units((5 / 8) * INCH), '5/8"'
        )
        self.assertEqual(
            imperial_fractional_drawing.number_with_units(math.pi * INCH), '3 9/64"'
        )
        imperial_fractional_drawing.fractional_precision = 16
        self.assertEqual(
            imperial_fractional_drawing.number_with_units(math.pi * INCH), '3 1/8"'
        )


if __name__ == "__main__":
    unittest.main()

# if __name__ == "__main__" or "show_object" in locals():
#     metric_drawing = Draft(decimal_precision=2)
#     print(metric_drawing.number_with_units(3.141))
#     print(metric_drawing.number_with_units(3.149))
#     print(metric_drawing.number_with_units(0))
#     imperial_drawing = Draft(units="imperial")
#     print(imperial_drawing.number_with_units((5 / 8) * INCH))
#     imperial_fractional_drawing = Draft(units="imperial", number_display="fraction")
#     print(imperial_fractional_drawing.number_with_units((5 / 8) * INCH))
#     print(imperial_fractional_drawing.number_with_units(pi * INCH))
#     draft_obj = Draft(font_size=5, color=cq.Color(0.75, 0.25, 0.25))
#     draft_obj_y = Draft(
#         font_size=8, color=cq.Color(0.75, 0.25, 0.25), label_normal=cq.Vector(0, -1, 0),
#     )
#     test0 = draft_obj.dimension_line(
#         path=((0, 0, 0), (40 * cos(pi / 6), -40 * sin(pi / 6), 0))
#     )
#     test1 = imperial_fractional_drawing.dimension_line(path=((-40, 0, 0), (40, 0, 0)))
#     test2 = draft_obj_y.dimension_line(
#         label="test2",
#         path=cq.Edge.makeThreePointArc(
#             cq.Vector(-40, 0, 0),
#             cq.Vector(-40 * sqrt(2) / 2, 0, 40 * sqrt(2) / 2),
#             cq.Vector(0, 0, 40),
#         ),
#     )
#     test3 = draft_obj_y.dimension_line(
#         label="test3",
#         path=cq.Edge.makeThreePointArc(
#             cq.Vector(0, 0, 40),
#             cq.Vector(40 * sqrt(2) / 2, 0, 40 * sqrt(2) / 2),
#             cq.Vector(40, 0, 0),
#         ),
#     )
#     test4 = draft_obj.dimension_line(
#         label="test4",
#         path=cq.Edge.makeThreePointArc(
#             cq.Vector(-40, 0, 0), cq.Vector(0, -40, 0), cq.Vector(40, 0, 0)
#         ),
#     )
#     draft_obj_oblique = Draft(
#         font_size=8,
#         color=cq.Color(0.75, 0.25, 0.25),
#         label_normal=cq.Vector(0, -0.5, 1),
#     )
#     test5 = draft_obj_oblique.dimension_line(
#         label="test5",
#         path=cq.Edge.makeSpline(
#             [cq.Vector(-40, 0, 0), cq.Vector(35, 20, 10), cq.Vector(40, 0, 0)]
#         ),
#     )
#     test6 = draft_obj.dimension_line(
#         label="test6", arrow_heads=[False, True], path=(cq.Vector(40, 0, 0), (80, 0, 0))
#     )
#     test7 = draft_obj.dimension_line(
#         label="test7",
#         arrow_heads=[True, False],
#         path=((-80, 0, 0), cq.Vector(-40, 0, 0)),
#     )
#     test8 = draft_obj.dimension_line(
#         label="test8",
#         arrow_heads=[True, False],
#         path=(cq.Vertex.makeVertex(0, -80, 0), cq.Vertex.makeVertex(0, -40, 0)),
#     )
#     test9 = draft_obj.extension_line(
#         label="test9",
#         object_edge=(cq.Vertex.makeVertex(0, -80, 0), cq.Vertex.makeVertex(0, -40, 0)),
#         offset=10 * MM,
#     )
#     test10 = draft_obj.extension_line(
#         label="80mm", object_edge=((-40, 0, 0), (40, 0, 0)), offset=30 * MM,
#     )
#     test11 = draft_obj.text_box(label="two\nlines", location=(40, 40, 0))
#     test12 = draft_obj.text_box(
#         label="look\nhere", location=(40, -40, 0), point_at=(0, -40, 0)
#     )
#     # with cProfile.Profile() as pr:
#     #     test3 = dimension_line("test3",
#     #         path=cq.Edge.makeThreePointArc(
#     #             cq.Vector(0,0,40),
#     #             cq.Vector(40*sqrt(2)/2,0,40*sqrt(2)/2),
#     #             cq.Vector(40,0,0)
#     #         )
#     #     )
#     # stats = pstats.Stats(pr)
#     # stats.sort_stats(pstats.SortKey.TIME)
#     # stats.print_stats()


# # If running from within the cq-editor, show the dimension_line lines
# if "show_object" in locals():
#     show_object(test0, name="test0")
#     show_object(test1, name="test1")
#     show_object(test2, name="test2")
#     show_object(test3, name="test3")
#     show_object(test4, name="test4")
#     show_object(test5, name="test5")
#     show_object(test6, name="test6")
#     show_object(test7, name="test7")
#     show_object(test8, name="test8")
#     show_object(test9, name="test9")
#     show_object(test10, name="test10")
#     show_object(test11, name="test11")
#     show_object(test12, name="test12")
