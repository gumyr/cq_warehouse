import cadquery as cq
from cq_warehouse.sprocket import Sprocket
from cq_warehouse.drafting import Draft

spkt = Sprocket(num_teeth=16)
title_draft = Draft(font_size=8, label_normal=(0, -3, 1))
title_line = title_draft.extension_line(
    object_edge=[(-spkt.outer_radius, 0, 0), (+spkt.outer_radius, 0, 0),],
    offset=-7,
    label="cq_warehouse",
)
svg_collection = cq.Assembly(None, name="collection")
svg_collection.add(spkt.cq_object)
svg_collection.add(title_line)
cq.exporters.export(
    svg_collection.toCompound(),
    fname="cq_title_image.svg",
    opt={
        "width": 200,
        "height": 500,
        "marginLeft": 35,
        "marginTop": 60,
        "projectionDir": (0, -3, 1),
        "showAxes": True,
        "strokeWidth": 0.1,
    },
)

if "show_object" in locals():
    show_object(spkt.cq_object, name="sprocket12")
    show_object(title_line, name="title_line")
