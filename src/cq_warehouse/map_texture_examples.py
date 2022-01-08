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
    projection_direction = cq.Vector(0, 0, 1)

    square = cq.Workplane("XY").rect(20, 20).extrude(1).faces("<Z").val()
    square_projected = square.projectToSolid(sphere, projection_direction)
    square_solids = cq.Compound.makeCompound([f.thicken(2) for f in square_projected])
    if "show_object" in locals():
        show_object(sphere, name="sphere_solid", options={"alpha": 0.8})
        show_object(square_solids, name="square_solids")

elif example == 5:
    projection_direction = cq.Vector(0, 0, 1)
    projection_plane = cq.Plane.named("XY")

    height = 50
    width = 100

    def surface(amplitude, u, v):
        """Calculate the surface displacement of the flag at a given position"""
        return v * amplitude / 20 * cos(3.5 * pi * u) + amplitude / 10 * v * sin(
            1.1 * pi * v
        )

    flag_surface = (
        cq.Workplane("XY")
        .parametricSurface(
            lambda u, v: cq.Vector(
                v * width,
                u * height,
                height * surface(2, u, v),
            ),
            N=40,
        )
        .thicken(1)
        .val()
    )
    # Canadian Flag raw dimensions 9600x4800
    west_field = cq.Workplane("XY").rect(2400, 4800, centered=False).wires().val()
    east_field = (
        cq.Workplane("XY")
        .center(7200, 0)
        .rect(2400, 4800, centered=False)
        .wires()
        .val()
    )
    maple_leaf = (
        cq.Workplane("XY")
        .moveTo(4890, 4430)
        .lineTo(4845, 3567)
        .radiusArc((4956, 3469), -130)
        .lineTo(5815, 3620)
        .lineTo(5699, 3300)
        .radiusArc((5719, 3227), -130)
        .lineTo(6660, 2465)
        .lineTo(6448, 2366)
        .radiusArc((6414, 2287), -130)
        .lineTo(6600, 1715)
        .lineTo(6058, 1830)
        .radiusArc((5985, 1792), -130)
        .lineTo(5880, 1545)
        .lineTo(5457, 1999)
        .radiusArc((5346, 1942), -130)
        .lineTo(5550, 890)
        .lineTo(5223, 1079)
        .radiusArc((5132, 1052), -130)
        .lineTo(4800, 400)
        .lineTo(4468, 1052)
        .radiusArc((4377, 1079), -130)
        .lineTo(4050, 890)
        .lineTo(4254, 1942)
        .radiusArc((4143, 1999), -130)
        .lineTo(3720, 1545)
        .lineTo(3615, 1792)
        .radiusArc((3542, 1830), -130)
        .lineTo(3000, 1715)
        .lineTo(3186, 2287)
        .radiusArc((3152, 2366), -130)
        .lineTo(2940, 2465)
        .lineTo(3881, 3227)
        .radiusArc((3901, 3300), -130)
        .lineTo(3785, 3620)
        .lineTo(4644, 3469)
        .radiusArc((4755, 3567), -130)
        .lineTo(4710, 4430)
        .close()
        .mirror("XZ")
        .translate((0, 4800, 0))
        .wires()
        .val()
    )
    flag_faces = [
        cq.Face.makeFromWires(w.scale(height / 4800), [])
        for w in [west_field, maple_leaf, east_field]
    ]
    for f in flag_faces:
        print(f"{f.isValid()}")
    maple_on_sphere = (
        flag_faces[1]
        .translate((-width / 2, -height / 2, 0))
        .projectToSolid(flag_surface, cq.Vector(0, 0, -1))
    )
    # projected_flag_faces = [
    #     # f.projectToSolid(flag_surface, cq.Vector(0, 0, -1)) for f in flag_faces
    #     f.projectToSolid(sphere, cq.Vector(0, 0, -1))[0]
    #     for f in flag_faces
    # ]
    # flag_image = cq.Compound.makeCompound(
    #     [f.thicken(3).translate((0, 0, -1.5)) for f in projected_flag_faces]
    # )

    if "show_object" in locals():
        show_object(sphere, name="sphere", options={"alpha": 0.8})
        # show_object(flag_surface, name="flag_surface", options={"alpha": 0.8})
        show_object(flag_faces[1], name="flag_faces")
        show_object(maple_on_sphere, name="maple_on_sphere")
        # show_object(projected_flag_faces, name="projected_flag_faces")
        # show_object(flag_image, name="flag_image")

else:
    """Example 6 - Compound Solid"""
    # complex_solid = (
    #     cq.Workplane("XY")
    #     .rect(100, 50)
    #     .rect(50, 100)
    #     .extrude(50, both=True)
    #     .edges("|Z")
    #     .fillet(10)
    # )

    # complex_solid_faces = complex_solid.faces().vals()
    # print(f"{len(complex_solid_faces)=}")
    # text_path = complex_solid.section().wires().val()
    # for i, f in enumerate(complex_solid_faces):
    #     print(f"{i}:{f.isInside(text_path.positionAt(0))}")
    # print(type(text_path))

    # text_on_complex = textOnSolid(
    #     txt="The quick brown fox jumped over the lazy dog",
    #     fontsize=10,
    #     distance=5,
    #     path=text_path,
    #     start=0,
    #     solid_object=complex_solid.val(),
    # )

    # if "show_object" in locals():
    #     show_object(xz_text_faces, name="text_faces")
    # show_object(complex_solid, name="complex_solid", options={"alpha": 0.8})
    # show_object(text_path, name="text_path")
    # show_object(text_on_complex, name="text_on_complex")
