"""
Example of placing a 20mm long screw into a 10mm deep hole
"""
import cadquery as cq
from cq_warehouse.fastener import SocketHeadCapScrew
import cq_warehouse.extensions

MM = 1
screw_alignment_assembly = cq.Assembly()
capscrew = SocketHeadCapScrew(
    size="M6-1", length=20 * MM, fastener_type="iso4762", simple=False
)
plate = (
    cq.Workplane("XY")
    .box(50 * MM, 50 * MM, 20 * MM)
    .faces(">Z")
    .clearanceHole(
        fastener=capscrew,
        depth=10 * MM,
        counterSunk=False,
        baseAssembly=screw_alignment_assembly,
    )
)
screw_alignment_assembly.add(plate, color=cq.Color("darkseagreen"))

if "show_object" in locals():
    show_object(screw_alignment_assembly, name="screw_alignment_assembly")
