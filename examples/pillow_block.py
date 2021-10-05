import cadquery as cq
from cq_warehouse.fastener import SocketHeadCapScrew

height = 60.0
width = 80.0
thickness = 10.0
diameter = 22.0
padding = 12.0

# make the screw
screw = SocketHeadCapScrew(screw_type="iso4762", size="M2-0.4", length=16)
# make the assembly
pillow_block = cq.Assembly(None, name="pillow_block")
# make the base
base = (
    cq.Workplane("XY")
    .box(height, width, thickness)
    .faces(">Z")
    .workplane()
    .hole(diameter)
    .faces(">Z")
    .workplane()
    .rect(height - padding, width - padding, forConstruction=True)
    .vertices()
    .clearanceHole(fastener=screw, baseAssembly=pillow_block)
)
pillow_block.add(base)
# Render the assembly
show_object(pillow_block)
