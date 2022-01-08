import timeit
import cadquery as cq
from map_texture import *

example = 5

sphere = cq.Solid.makeSphere(50, angleDegrees1=-90)


def make_text_faces(txt: str, plane: str, fontsize: float = 20) -> list[cq.Face]:
    selector = {"XY": "<Z", "XZ": ">Y"}
    return (
        cq.Workplane(plane)
        .text(
            txt,
            fontsize=fontsize,
            distance=1,
            font="Serif",
            fontPath="/usr/share/fonts/truetype/freefont",
            halign="center",
        )
        .faces(selector[plane])
        .vals()
    )


if example == 1:
    """Example 1 - Flat Projection of Text on Sphere"""
    starttime = timeit.default_timer()

    projection_direction = cq.Vector(0, 1, 0)
    text_faces = make_text_faces("Beingφθ⌀", "XZ")

    projected_text_faces = [
        f.projectToSolid(sphere, projection_direction)[BACK] for f in text_faces
    ]
    projected_text = cq.Compound.makeCompound(
        [f.thicken(-5, direction=projection_direction) for f in projected_text_faces]
    )
    print(f"Example #{example} time: {timeit.default_timer() - starttime:0.2f}s")
    if "show_object" in locals():
        show_object(sphere, name="sphere_solid", options={"alpha": 0.8})
        show_object(text_faces, name="text_faces")
        show_object(projected_text, name="projected_sphere_text_solid")


elif example == 2:
    """Example 2 - Conical Projection of Text on Sphere"""
    starttime = timeit.default_timer()

    projection_center = cq.Vector(0, 700, 0)
    text_faces = make_text_faces("φθ⌀ #" + str(example), "XZ")
    text_faces = [f.translate((0, -60, 0)) for f in text_faces]

    projected_text_faces = [
        f.projectToSolid(sphere, center=projection_center)[FRONT] for f in text_faces
    ]
    projected_text = cq.Compound.makeCompound(
        [
            f.thicken(-5, direction=text_faces[0].Center() - projection_center)
            for f in projected_text_faces
        ]
    )
    print(f"Example #{example} time: {timeit.default_timer() - starttime:0.2f}s")
    if "show_object" in locals():
        show_object(sphere, name="sphere_solid", options={"alpha": 0.8})
        show_object(text_faces, name="text_faces")
        show_object(projected_text_faces, name="projected_text_faces")
        show_object(projected_text, name="projected_sphere_text_solid")
        show_object(
            cq.Vertex.makeVertex(*projection_center.toTuple()), name="projection center"
        )


elif example == 3:
    """Example 3 - Mapping Text on Cylinder"""
    starttime = timeit.default_timer()

    text_faces = make_text_faces(
        "Example #" + str(example) + " Cylinder Wrap ⌀100", "XY"
    )
    projected_text_faces = [f.projectToCylinder(radius=50) for f in text_faces]
    projected_text = cq.Compound.makeCompound(
        [f.thicken(5, f.Center()) for f in projected_text_faces]
    )
    print(f"Example #{example} time: {timeit.default_timer() - starttime:0.2f}s")
    if "show_object" in locals():
        show_object(
            cq.Solid.makeCylinder(50, 100, cq.Vector(0, 0, -50)),
            name="sphere_solid",
            options={"alpha": 0.8},
        )
        show_object(text_faces, name="text_faces")
        show_object(projected_text, name="projected_text")

elif example == 4:
    """Example 4 - Mapping A Face on Sphere"""
    starttime = timeit.default_timer()
    projection_direction = cq.Vector(0, 0, 1)

    square = cq.Workplane("XY").rect(20, 20).extrude(1).faces("<Z").val()
    square_projected = square.projectToSolid(sphere, projection_direction)
    square_solids = cq.Compound.makeCompound([f.thicken(2) for f in square_projected])
    print(f"Example #{example} time: {timeit.default_timer() - starttime:0.2f}s")
    if "show_object" in locals():
        show_object(sphere, name="sphere_solid", options={"alpha": 0.8})
        show_object(square_solids, name="square_solids")

elif example == 5:
    """Example 5 - A Canadian Flag blowing in the wind"""
    starttime = timeit.default_timer()

    # Canadian Flags have a 2:1 aspect ratio
    height = 50
    width = 2 * height
    wave_amplitude = 3

    def surface(amplitude, u, v):
        """Calculate the surface displacement of the flag at a given position"""
        return v * amplitude / 20 * cos(3.5 * pi * u) + amplitude / 10 * v * sin(
            1.1 * pi * v
        )

    # Note that the surface to project on must be a little larger than the faces
    # being projected onto it to create valid projected faces
    flag_surface = (
        cq.Workplane("XY")
        .parametricSurface(
            lambda u, v: cq.Vector(
                v * width * 1.01,
                u * height * 1.01,
                height * surface(wave_amplitude, u, v) / 2,
            ),
            N=40,
        )
        .thicken(0.5)
        .translate((-width * 0.005, -height * 0.005, 0))
        .val()
    )
    west_field = (
        cq.Workplane("XY")
        .center(-1, 0)
        .rect(0.5, 1, centered=False)
        .wires()
        .val()
        .scale(height)
    )
    east_field = west_field.mirror("YZ")
    center_field = (
        cq.Workplane("XY")
        .center(-0.5, 0)
        .rect(1, 1, centered=False)
        .wires()
        .val()
        .scale(height)
    )
    maple_leaf = (
        cq.Workplane("XY")
        .moveTo(0.0000, 0.0771)
        .lineTo(0.0187, 0.0771)
        .lineTo(0.0094, 0.2569)
        .radiusArc((0.0325, 0.2773), 0.0271)
        .lineTo(0.2115, 0.2458)
        .lineTo(0.1873, 0.3125)
        .radiusArc((0.1915, 0.3277), 0.0271)
        .lineTo(0.3875, 0.4865)
        .lineTo(0.3433, 0.5071)
        .radiusArc((0.3362, 0.5235), 0.0271)
        .lineTo(0.375, 0.6427)
        .lineTo(0.2621, 0.6188)
        .radiusArc((0.2469, 0.6267), 0.0271)
        .lineTo(0.225, 0.6781)
        .lineTo(0.1369, 0.5835)
        .radiusArc((0.1138, 0.5954), 0.0271)
        .lineTo(0.1562, 0.8146)
        .lineTo(0.0881, 0.7752)
        .radiusArc((0.0692, 0.7808), 0.0271)
        .lineTo(0.0, 0.9167)
        .mirrorY()
        .wires()
        .val()
        .scale(height)
    )
    flag_faces = [
        cq.Face.makeFromWires(w, []).translate(cq.Vector(width / 2, 0, 30))
        for w in [west_field, maple_leaf, east_field]
    ]
    flag_faces.append(
        cq.Face.makeFromWires(center_field, [maple_leaf]).translate(
            cq.Vector(width / 2, 0, 30)
        )
    )
    projected_flag_faces = [
        f.projectToSolid(flag_surface, cq.Vector(0, 0, -1))[FRONT] for f in flag_faces
    ]
    flag_parts = [f.thicken(1.5, cq.Vector(0, 0, 1)) for f in projected_flag_faces]
    print(f"Example #{example} time: {timeit.default_timer() - starttime:0.2f}s")

    if "show_object" in locals():
        show_object(flag_surface, name="flag_surface", options={"alpha": 0.8})
        show_object(
            flag_parts[0:-1], name="flag_red_parts", options={"color": (255, 0, 0)}
        )
        show_object(
            flag_parts[-1], name="flag_white_part", options={"color": (255, 255, 255)}
        )

else:
    """Example 6 - Compound Solid - under construction"""
    compound_solid = (
        cq.Workplane("XY")
        .rect(100, 50)
        .rect(50, 100)
        .extrude(50, both=True)
        .edges("|Z")
        .fillet(10)
    )

    compound_solid_faces = compound_solid.faces().vals()
    print(f"{len(compound_solid_faces)=}")
    text_path = compound_solid.section().wires().val()
    for i, f in enumerate(compound_solid_faces):
        print(f"{i}:{f.isInside(text_path.positionAt(0))}")
    print(type(text_path))

    # text_on_compound = textOnSolid(
    #     txt="The quick brown fox jumped over the lazy dog",
    #     fontsize=10,
    #     distance=5,
    #     path=text_path,
    #     start=0,
    #     solid_object=compound_solid.val(),
    # )

    if "show_object" in locals():
        show_object(compound_solid, name="compound_solid", options={"alpha": 0.8})
        show_object(text_path, name="text_path")
        show_object(text_on_compound, name="text_on_compound")
