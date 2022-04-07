import cadquery as cq
from cq_warehouse.fastener import SocketHeadCapScrew
from cq_warehouse.bearing import SingleRowDeepGrooveBallBearing
import cq_warehouse.extensions

height = 60.0
width = 80.0
thickness = 10.0
padding = 12.0

# make the bearing
bearing = SingleRowDeepGrooveBallBearing(size="M8-22-7", bearing_type="SKT")
# make the screw
screw = SocketHeadCapScrew(
    size="M2-0.4", fastener_type="iso4762", length=16, simple=False
)
# make the assembly
pillow_block = cq.Assembly(None, name="pillow_block")
# make the base
base = (
    cq.Workplane("XY")
    .box(height, width, thickness)
    .faces(">Z")
    .workplane()
    .pressFitHole(bearing=bearing, baseAssembly=pillow_block)
    .faces(">Z")
    .workplane()
    .rect(height - padding, width - padding, forConstruction=True)
    .vertices()
    .clearanceHole(fastener=screw, baseAssembly=pillow_block)
    .edges("|Z")
    .fillet(2.0)
)
pillow_block.add(base, name="base", color=cq.Color(162 / 255, 138 / 255, 255 / 255))
print(pillow_block.fastenerQuantities())

# Render the assembly
if "show_object" in locals():
    show_object(pillow_block)
