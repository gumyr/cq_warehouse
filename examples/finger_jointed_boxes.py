import cadquery as cq
import cq_warehouse.extensions

# Create an empty assembly which will be populated with the finger jointed box
polygon_box_assembly = cq.Assembly()

# Create the box shape and then the finger jointed faces
polygon_box_faces = (
    cq.Workplane("XY")
    .polygon(5, 100)
    .extrude(60)
    .edges("not >Z")
    .makeFingerJoints(
        materialThickness=5,
        targetFingerWidth=20,
        kerfWidth=0,
        baseAssembly=polygon_box_assembly,
    )
)
# Is the finger jointed box valid?
print(f"{polygon_box_assembly.areObjectsValid()=}")
print(f"{polygon_box_assembly.doObjectsIntersect()=}")

# Store the faces as DXF files
for i, box_face in enumerate(polygon_box_faces.faces().vals()):
    center = box_face.Center()
    face_plane = cq.Plane(origin=center, normal=box_face.normalAt(center))
    face_workplane = cq.Workplane(face_plane).add(box_face)
    cq.exporters.export(face_workplane, fname="box_face" + str(i) + ".DXF")

if "show_object" in locals():
    show_object(polygon_box_assembly, name="polygon_box_assembly")
