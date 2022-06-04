import cadquery as cq
from cq_warehouse.fastener import HexNut, SquareNut
import cq_warehouse.extensions

hex_nut = HexNut(size="M6-1", fastener_type="iso4033")
square_nut = SquareNut(size="M6-1", fastener_type="din557")
test_assembly = cq.Assembly()
block = (
    cq.Workplane("XY")
    .box(50, 50, 10)
    .faces(">Z")
    .workplane()
    .pushPoints([(-12.5, 0)])
    .clearanceHole(
        fastener=hex_nut, fit="Loose", captiveNut=True, baseAssembly=test_assembly
    )
    .pushPoints([(+12.5, 0)])
    .clearanceHole(fastener=square_nut, captiveNut=True, baseAssembly=test_assembly)
)
test_assembly.add(block, color=cq.Color("tan"))

if "show_object" in locals():
    show_object(test_assembly, name="test_assembly")
