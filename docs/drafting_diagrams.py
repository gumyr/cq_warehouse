import math
import cadquery as cq
from cq_warehouse.drafting import Draft

corners = [0, 10, 40, 50, 70, 90, 95, 155, 160, 170]


def height(i):
    base = 60 if i == 0 or i == len(corners) - 1 else 40
    return [base, 20] if i % 2 == 0 else [20, base]


linear_teeth = [(x, y) for i, x in enumerate(corners) for y in height(i)]

linear_object = cq.Workplane("XY").polyline(linear_teeth).close().extrude(2)
vertices = sorted(
    linear_object.vertices("<Z and <Y").vals(), key=lambda vertex: vertex.X
)

metric_drawing = Draft(decimal_precision=0)
linear_measure_type_1 = metric_drawing.extension_line(
    label="Type 1", object_edge=[vertices[1], vertices[2]], offset=10
)
linear_measure_type_2 = metric_drawing.extension_line(
    label="Type 2", object_edge=[vertices[3], vertices[4]], offset=10
)
linear_measure_type_3a = metric_drawing.extension_line(
    label="Type 3a", object_edge=[vertices[5], vertices[6]], offset=10
)
linear_measure_type_3b = metric_drawing.extension_line(
    label="Type 3b",
    object_edge=[vertices[7], vertices[8]],
    offset=10,
    arrows=[True, False],
)


def circle_point(angle, radius):
    return (
        radius * math.cos(math.radians(angle)),
        radius * math.sin(math.radians(angle)),
    )


r0 = 90
r1 = 100
angles = [
    -86,
    -68,
    -60,
    -50,
    -40,
    -37,
    -8,
    -5,
    0,
]
arc_object = (
    cq.Workplane("XY")
    .vLineTo(-r1)
    .radiusArc(circle_point(angles[0], r1), -r1)
    .lineTo(*circle_point(angles[0], r0))
    .radiusArc(circle_point(angles[1], r0), -r0)
    .lineTo(*circle_point(angles[1], r1))
    .radiusArc(circle_point(angles[2], r1), -r1)
    .lineTo(*circle_point(angles[2], r0))
    .radiusArc(circle_point(angles[3], r0), -r0)
    .lineTo(*circle_point(angles[3], r1))
    .radiusArc(circle_point(angles[4], r1), -r1)
    .lineTo(*circle_point(angles[4], r0))
    .radiusArc(circle_point(angles[5], r0), -r0)
    .lineTo(*circle_point(angles[5], r1))
    .radiusArc(circle_point(angles[6], r1), -r1)
    .lineTo(*circle_point(angles[6], r0))
    .radiusArc(circle_point(angles[7], r0), -r0)
    .lineTo(*circle_point(angles[7], r1))
    .radiusArc(circle_point(angles[8], r1), -r1)
    .close()
    .extrude(2)
)
arc1 = cq.Edge.makeCircle(r1, angle1=angles[0], angle2=angles[1])
arc_measure_type_1 = metric_drawing.extension_line(
    label="Type 1", object_edge=arc1, offset=10
)
arc2 = cq.Edge.makeCircle(r1, angle1=angles[2], angle2=angles[3])
arc_measure_type_2 = metric_drawing.extension_line(
    label="Type 2", object_edge=arc2, offset=10
)
arc3a = cq.Edge.makeCircle(r1, angle1=angles[4], angle2=angles[5])
arc_measure_type_3a = metric_drawing.extension_line(
    label="Type 3a", object_edge=arc3a, offset=10
)
arc3b = cq.Edge.makeCircle(r1, angle1=angles[6], angle2=angles[7])
arc_measure_type_3b = metric_drawing.extension_line(
    label="Type 3b", object_edge=arc3b, offset=10, arrows=[True, False]
)


if "show_object" in locals():
    show_object(linear_object, name="linear_object")
    show_object(linear_measure_type_1, name="linear_measure_type_1")
    show_object(linear_measure_type_2, name="linear_measure_type_2")
    show_object(linear_measure_type_3a, name="linear_measure_type_3a")
    show_object(linear_measure_type_3b, name="linear_measure_type_3b")
    show_object(arc_object, name="arc_object")
    show_object(arc_measure_type_1, name="arc_measure_type_1")
    show_object(arc_measure_type_2, name="arc_measure_type_2")
    show_object(arc_measure_type_3a, name="arc_measure_type_3a")
    show_object(arc_measure_type_3b, name="arc_measure_type_3b")
