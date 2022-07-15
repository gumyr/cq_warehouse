# -*- coding: utf-8 -*-
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
import cadquery as cq
from cq_warehouse.drafting import Draft

MM = 1
INCH = 25.4 * MM


def _assertTupleAlmostEquals(self, expected, actual, places, msg=None):
    """Check Tuples"""
    for i, j in zip(actual, expected):
        self.assertAlmostEqual(i, j, places, msg=msg)


unittest.TestCase.assertTupleAlmostEquals = _assertTupleAlmostEquals


class TestClassInstantiation(unittest.TestCase):

    """Test Draft class instantiation"""

    def test_draft_instantiation(self):
        """Parameter parsing"""
        with self.assertRaises(ValueError):
            Draft(units="normal")
        with self.assertRaises(ValueError):
            Draft(number_display="normal")
        with self.assertRaises(ValueError):
            Draft(units="imperial", number_display="fraction", fractional_precision=37)


class TestFunctionality(unittest.TestCase):
    """Test core drafting functionality"""

    def test_number_with_units(self):
        metric_drawing = Draft(decimal_precision=2)
        self.assertEqual(metric_drawing._number_with_units(3.141), "3.14mm")
        self.assertEqual(metric_drawing._number_with_units(3.149), "3.15mm")
        self.assertEqual(metric_drawing._number_with_units(0), "0.00mm")
        self.assertEqual(
            metric_drawing._number_with_units(3.14, tolerance=0.01), "3.14 ±0.01mm"
        )
        self.assertEqual(
            metric_drawing._number_with_units(3.14, tolerance=(0.01, 0)),
            "3.14 +0.01 -0.00mm",
        )
        whole_number_drawing = Draft(decimal_precision=-1)
        self.assertEqual(whole_number_drawing._number_with_units(314.1), "310mm")

        imperial_drawing = Draft(units="imperial")
        self.assertEqual(imperial_drawing._number_with_units((5 / 8) * INCH), '0.62"')
        imperial_fractional_drawing = Draft(
            units="imperial", number_display="fraction", fractional_precision=64
        )
        self.assertEqual(
            imperial_fractional_drawing._number_with_units((5 / 8) * INCH), '5/8"'
        )
        self.assertEqual(
            imperial_fractional_drawing._number_with_units(math.pi * INCH), '3 9/64"'
        )
        imperial_fractional_drawing.fractional_precision = 16
        self.assertEqual(
            imperial_fractional_drawing._number_with_units(math.pi * INCH), '3 1/8"'
        )

    def test_label_to_str(self):
        metric_drawing = Draft(decimal_precision=0)
        line = cq.Edge.makeLine(cq.Vector(0, 0, 0), cq.Vector(100, 0, 0))
        with self.assertRaises(ValueError):
            metric_drawing._label_to_str(
                label=None,
                line_wire=line,
                label_angle=True,
                tolerance=0,
            )
        arc1 = cq.Edge.makeCircle(100, angle1=0, angle2=30)
        angle_str = metric_drawing._label_to_str(
            label=None,
            line_wire=arc1,
            label_angle=True,
            tolerance=0,
        )
        self.assertEqual(angle_str, "30°")

    def test_segment_line_exceptions(self):
        line_edge = cq.Edge.makeLine(cq.Vector(0, 0, 0), cq.Vector(0, 0, 1))
        line_wire = cq.Wire.assembleEdges([line_edge])
        with self.assertRaises(ValueError):
            Draft._segment_line(path=line_edge, tip_pos=-1.0, tail_pos=1.0)
        with self.assertRaises(ValueError):
            Draft._segment_line(path=line_wire, tip_pos=2.0, tail_pos=1.0)
        with self.assertRaises(ValueError):
            Draft._segment_line(path=line_edge, tip_pos=0.0, tail_pos=-1.0)
        with self.assertRaises(ValueError):
            Draft._segment_line(path=line_edge, tip_pos=0.0, tail_pos=2.0)

    def test_project_wire(self):
        wire = Draft._path_to_wire(((0,0,0), (10,10,0)))
        projected_wire = Draft._project_wire(wire, (0,1,0))
        self.assertEqual(projected_wire.startPoint(), cq.Vector(0,0,0))
        self.assertEqual(projected_wire.endPoint(), cq.Vector(0,10,0))
        self.assertNotEqual(wire, projected_wire)

    def test_path_to_wire(self):
        wire = Draft._path_to_wire(((0,0,0), (10,10,0)))
        self.assertIsInstance(wire, cq.Wire)
        self.assertEqual(cq.Vector(0,0,0), wire.startPoint())
        self.assertEqual(cq.Vector(10,10,0), wire.endPoint())

    def test_extension_line_with_dimension_gap(self):
        metric_drawing = Draft(
            decimal_precision=0,
            extension_gap=10
        )
        self.assertEqual(metric_drawing.extension_gap, 10)
        arc_measure_type_1 = metric_drawing.extension_line(
            label="Type 1", object_edge=[(0, 0, 0), (100, 0, 0)], offset=10
        )
        self.assertEqual(arc_measure_type_1.name, "Type 1_extension_line")
        self.assertEqual(len(arc_measure_type_1.children), 3)
        self.assertEqual(arc_measure_type_1.children[0].name, "extension_line0")
        self.assertEqual(arc_measure_type_1.children[1].name, "extension_line1")
        self.assertEqual(arc_measure_type_1.children[2].name, "dimension_line")
        self.assertEqual(
            arc_measure_type_1.children[1].obj.val().startPoint(),
            cq.Vector(100,-10,0)
        )

    def test_extension_line(self):
        metric_drawing = Draft(decimal_precision=0)
        arc_measure_type_1 = metric_drawing.extension_line(
            label="Type 1", object_edge=[(0, 0, 0), (100, 0, 0)], offset=10
        )
        self.assertEqual(arc_measure_type_1.name, "Type 1_extension_line")
        self.assertEqual(len(arc_measure_type_1.children), 3)
        self.assertEqual(arc_measure_type_1.children[0].name, "extension_line0")
        self.assertEqual(arc_measure_type_1.children[1].name, "extension_line1")
        self.assertEqual(arc_measure_type_1.children[2].name, "dimension_line")
        self.assertEqual(
            arc_measure_type_1.children[1].obj.val().startPoint(),
            cq.Vector(100,0,0)
        )

    def test_extension_line_with_projection(self):
        metric_drawing = Draft(decimal_precision=0)
        arc_measure_type_1 = metric_drawing.extension_line(
            label="Type 1", 
            object_edge=[(0, 0, 0), (100, 100, 0)], 
            offset=10,
            project_line=(0,1,0)
        )
        self.assertEqual(arc_measure_type_1.name, "Type 1_extension_line")
        self.assertEqual(len(arc_measure_type_1.children), 3)
        self.assertEqual(arc_measure_type_1.children[0].name, "extension_line0")
        self.assertEqual(arc_measure_type_1.children[1].name, "extension_line1")
        self.assertEqual(arc_measure_type_1.children[2].name, "dimension_line")
        self.assertEqual(
            arc_measure_type_1.children[1].obj.val().startPoint(),
            cq.Vector(100,100,0)
        )

    def test_extension_line_arc(self):
        metric_drawing = Draft(decimal_precision=0)
        arc1 = cq.Edge.makeCircle(100, angle1=10, angle2=30)
        arc_measure_type_1 = metric_drawing.extension_line(
            label="Type 1", object_edge=arc1, offset=10
        )
        self.assertEqual(arc_measure_type_1.name, "Type 1_extension_line")
        self.assertEqual(len(arc_measure_type_1.children), 3)
        self.assertEqual(arc_measure_type_1.children[0].name, "extension_line0")
        self.assertEqual(arc_measure_type_1.children[1].name, "extension_line1")
        self.assertEqual(arc_measure_type_1.children[2].name, "dimension_line")

        arc2 = cq.Edge.makeCircle(100, angle1=20, angle2=30)
        arc_measure_type_2 = metric_drawing.extension_line(
            label="Type 2", object_edge=arc2, offset=10
        )
        self.assertEqual(arc_measure_type_2.name, "Type 2_extension_line")
        self.assertEqual(len(arc_measure_type_2.children), 3)
        self.assertEqual(arc_measure_type_2.children[0].name, "extension_line0")
        self.assertEqual(arc_measure_type_2.children[1].name, "extension_line1")
        self.assertEqual(arc_measure_type_2.children[2].name, "dimension_line")
        arc3a = cq.Edge.makeCircle(100, angle1=30, angle2=33)
        arc_measure_type_3a = metric_drawing.extension_line(
            label="Type 3a", object_edge=arc3a, offset=10
        )
        self.assertEqual(arc_measure_type_3a.name, "Type 3a_extension_line")
        self.assertEqual(len(arc_measure_type_3a.children), 3)
        self.assertEqual(arc_measure_type_3a.children[0].name, "extension_line0")
        self.assertEqual(arc_measure_type_3a.children[1].name, "extension_line1")
        self.assertEqual(arc_measure_type_3a.children[2].name, "dimension_line")
        arc3b = cq.Edge.makeCircle(100, angle1=30, angle2=33)
        arc_measure_type_3b = metric_drawing.extension_line(
            label="Type 3b", object_edge=arc3b, offset=10, arrows=[True, False]
        )
        self.assertEqual(arc_measure_type_3b.name, "Type 3b_extension_line")
        self.assertEqual(len(arc_measure_type_3b.children), 3)
        self.assertEqual(arc_measure_type_3b.children[0].name, "extension_line0")
        self.assertEqual(arc_measure_type_3b.children[1].name, "extension_line1")
        self.assertEqual(arc_measure_type_3b.children[2].name, "dimension_line")

        with self.assertRaises(ValueError):
            metric_drawing.extension_line(
                label="Type 3b", object_edge=arc3b, offset=10, arrows=[False, False]
            )

    def test_dimension_line(self):
        metric_drawing = Draft(decimal_precision=1)
        line = cq.Edge.makeLine(cq.Vector(0, 0, 0), cq.Vector(100, 0, 0))
        linear_measure_type_1 = metric_drawing.dimension_line(path=line, tolerance=0.1)
        self.assertEqual(linear_measure_type_1.name, "100.0 ±0.1mm_dimension_line")
        self.assertEqual(len(linear_measure_type_1.children), 3)
        self.assertEqual(linear_measure_type_1.children[0].name, "start_arrow")
        self.assertEqual(linear_measure_type_1.children[1].name, "end_arrow")
        self.assertEqual(linear_measure_type_1.children[2].name, "label")

        linear_measure_type_1 = metric_drawing.dimension_line(
            path=[(0, 0, 0), (50, 0, 0)]
        )
        self.assertEqual(linear_measure_type_1.name, "50.0mm_dimension_line")
        self.assertEqual(len(linear_measure_type_1.children), 3)
        self.assertEqual(linear_measure_type_1.children[0].name, "start_arrow")
        self.assertEqual(linear_measure_type_1.children[1].name, "end_arrow")
        self.assertEqual(linear_measure_type_1.children[2].name, "label")

        with self.assertRaises(ValueError):
            metric_drawing.dimension_line(
                path=[(0, 0, 0), (50, 0, 0)], label_angle=True
            )

    def test_callout(self):
        metric_drawing = Draft()
        title = metric_drawing.callout(label="test", origin=(0, 0, 0))
        self.assertEqual(title.name, "test_callout")
        self.assertEqual(len(title.children), 1)
        self.assertEqual(title.children[0].name, "callout_label")

        note = metric_drawing.callout(label="note", tail=[(0, 0, 0), (100, 100, 0)])
        self.assertEqual(note.name, "note_callout")
        self.assertEqual(len(note.children), 2)
        self.assertEqual(note.children[0].name, "callout_label")
        self.assertEqual(note.children[1].name, "callout_tail")

        with self.assertRaises(ValueError):
            metric_drawing.callout(label="error")

        with self.assertRaises(TypeError):
            metric_drawing.callout(label="test", location=(0, 0, 0), justify="centre")


class TestVertexExtensions(unittest.TestCase):
    """Test the extensions to the cadquery Vertex class"""

    def test_vertex_add(self):
        test_vertex = cq.Vertex.makeVertex(0, 0, 0)
        self.assertTupleAlmostEquals(
            (test_vertex + (100, -40, 10)).toTuple(), (100, -40, 10), 7
        )
        self.assertTupleAlmostEquals(
            (test_vertex + cq.Vector(100, -40, 10)).toTuple(), (100, -40, 10), 7
        )
        self.assertTupleAlmostEquals(
            (test_vertex + cq.Vertex.makeVertex(100, -40, 10)).toTuple(),
            (100, -40, 10),
            7,
        )
        with self.assertRaises(TypeError):
            test_vertex + [1, 2, 3]

    def test_vertex_sub(self):
        test_vertex = cq.Vertex.makeVertex(0, 0, 0)
        self.assertTupleAlmostEquals(
            (test_vertex - (100, -40, 10)).toTuple(), (-100, 40, -10), 7
        )
        self.assertTupleAlmostEquals(
            (test_vertex - cq.Vector(100, -40, 10)).toTuple(), (-100, 40, -10), 7
        )
        self.assertTupleAlmostEquals(
            (test_vertex - cq.Vertex.makeVertex(100, -40, 10)).toTuple(),
            (-100, 40, -10),
            7,
        )
        with self.assertRaises(TypeError):
            test_vertex - [1, 2, 3]

    def test_vertex_str(self):
        self.assertEqual(str(cq.Vertex.makeVertex(0, 0, 0)), "Vertex: (0.0, 0.0, 0.0)")

    def test_vertex_to_vector(self):
        self.assertIsInstance(cq.Vertex.makeVertex(0, 0, 0).toVector(), cq.Vector)
        self.assertTupleAlmostEquals(
            cq.Vertex.makeVertex(0, 0, 0).toVector().toTuple(), (0.0, 0.0, 0.0), 7
        )


if __name__ == "__main__":
    unittest.main()
