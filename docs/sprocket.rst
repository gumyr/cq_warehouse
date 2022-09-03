###############################
sprocket - parametric sprockets
###############################
A sprocket can be generated and saved to a STEP file with just four lines
of python code using the :ref:`Sprocket <sprocket>` class:

.. code-block:: python

   import cadquery as cq
   from cq_warehouse.sprocket import Sprocket

   sprocket32 = Sprocket(num_teeth=32)
   cq.exporters.export(sprocket32,"sprocket.step")


How does this code work?

#. The first line imports cadquery CAD system with the alias cq
#. The second line imports the Sprocket class from the sprocket sub-package of the cq_warehouse package
#. The third line instantiates a 32 tooth sprocket named "sprocket32"
#. The fourth line uses the cadquery exporter functionality to save the generated
   sprocket object in STEP format

.. deprecated:: 0.8

	Previous versions of cq_warehouse required the used of a ``cq_object`` instance variable to access
	the CadQuery cad object. Currently sprocket objects are a sub-class of the CadQuery Solid
	object and therefore can be used as any other Solid object without referencing ``cq_object``.
	Future versions of cq_warehouse will remove ``cq_object`` entirely.

.. py:module:: sprocket

.. _sprocket:

.. autoclass:: Sprocket
	:members: sprocket_pitch_radius, sprocket_circumference

Most of the Sprocket parameters are shown in the following diagram:

.. image:: sprocket_dimensions.png
	:alt: sprocket parameters



The sprocket in the diagram was generated as follows:

.. code-block:: python

	MM = 1
	chain_ring = Sprocket(
	    num_teeth = 32,
	    clearance = 0.1 * MM,
	    bolt_circle_diameter = 104 * MM,
	    num_mount_bolts = 4,
	    mount_bolt_diameter = 10 * MM,
	    bore_diameter = 80 * MM
	)

.. note::

	Units in CadQuery are defined so that 1 represents one millimeter but ``MM = 1`` makes this
	explicit.


Tooth Tip Shape
===============
Normally the tip of a sprocket tooth has a circular section spanning the roller pin sockets
on either side of the tooth tip. In this case, the tip is chamfered to allow the chain to
easily slide over the tooth tip thus reducing the chances of derailing the chain in normal
operation. However, it is valid to generate a sprocket without this "flat" section by
increasing the size of the rollers. In this case, the tooth tips will be "spiky" and
will not be chamfered.
