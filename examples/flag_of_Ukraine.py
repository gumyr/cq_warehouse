"""Flag of Ukraine"""
from math import sin, cos, pi
import cadquery as cq
import cq_warehouse.extensions

# Ukrainian Flags have a 2:3 aspect ratio
height = 50
width = 1.5 * height
wave_amplitude = 3
BLUE = (0, 87, 183)
YELLOW = (255, 215, 0)


def surface(amplitude, u, v):
    """Calculate the surface displacement of the flag at a given position"""
    return v * amplitude / 20 * cos(3.5 * pi * u) + amplitude / 10 * v * sin(
        1.1 * pi * v
    )


the_wind = (
    cq.Workplane("XY")
    .parametricSurface(
        lambda u, v: cq.Vector(
            width * (v * 1.1 - 0.05),
            height * (u * 1.2 - 0.1),
            height * surface(wave_amplitude, u, v) / 2,
        ),
        N=40,
    )
    .thicken(0.5)
    .val()
)

top_face = (
    cq.Sketch()
    .push([(width / 2, 3 * height / 4)])
    .rect(width, height / 2)
    ._faces.Faces()[0]
    .translate(cq.Vector(0, 0, height / 2))
)
bottom_face = top_face.mirror("XZ", basePointVector=(0, height / 2, 0))
projected_top_face = top_face.projectToShape(the_wind, direction=cq.Vector(0, 0, -1))[0]
projected_bottom_face = bottom_face.projectToShape(
    the_wind, direction=cq.Vector(0, 0, -1)
)[0]
flag_segment_top = projected_top_face.thicken(1).rotate(
    cq.Vector(0, 0, 0), cq.Vector(1, 0, 0), 90
)
flag_segment_bottom = projected_bottom_face.thicken(1).rotate(
    cq.Vector(0, 0, 0), cq.Vector(1, 0, 0), 90
)

if "show_object" in locals():
    show_object(flag_segment_top, name="flag_blue_part", options={"color": BLUE})
    show_object(flag_segment_bottom, name="flag_yellow_part", options={"color": YELLOW})
