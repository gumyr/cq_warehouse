
####################################
chain - a parametric chain generator
####################################
A chain wrapped around a set of sprockets can be generated with the :ref:`Chain<chain>` class by providing
the size and locations of the sprockets, how the chain wraps and optionally the chain parameters.

For example, one can create the chain for a bicycle with a rear deraileur as follows:

.. code-block:: python

	import cadquery as cq
	import cq_warehouse.chain as Chain

	derailleur_chain = Chain(
	    spkt_teeth=[32, 10, 10, 16],
	    positive_chain_wrap=[True, True, False, True],
	    spkt_locations=[
	        (0, 158.9 * MM, 50 * MM),
	        (+190 * MM, 0, 50 * MM),
	        (+190 * MM, 78.9 * MM, 50 * MM),
	        (+205 * MM, 158.9 * MM, 50 * MM)
	    ]
	)
	if "show_object" in locals():
	    show_object(derailleur_chain.cq_object, name="derailleur_chain")

The chain is created on the XY plane (methods to move the chain are described below)
with the sprocket centers being described by:

* a two dimensional tuple (x,y)
* a three dimensional tuple (x,y,z) which will result in the chain being created parallel
  to the XY plane, offset by "z"
* the cadquery Vector class which will displace the chain by Vector.z

To control the path of the chain between the sprockets, the user must indicate the desired
direction for the chain to wrap around the sprocket. This is done with the ``positive_chain_wrap``
parameter which is a list of boolean values - one for each sprocket - indicating a counter
clock wise or positive angle around the z-axis when viewed from the positive side of the XY
plane. The following diagram illustrates the most complex chain path where the chain
traverses wraps from positive to positive, positive to negative, negative to positive and
negative to negative directions (`positive_chain_wrap` values are shown within the arrows
starting from the largest sprocket):

.. image:: chain_direction.png
	:alt: chain direction

.. py:module:: chain

.. _chain:

.. autoclass:: Chain
	:members: assemble_chain_transmission, make_link

Note that the chain is perfectly tight as it wraps around the sprockets and does
not support any slack. Therefore, as the chain wraps back around to the first
link it will either overlap or gap this link - this can be seen in the above
figure at the top of the largest sprocket. Adjust the locations of the sprockets
to control this value.

Note that the make_link instance method uses the @cache decorator to greatly improve the rate at
links can be generated as a chain is composed of many copies of the links.

Once a chain or complete transmission has been generated it can be re-oriented as follows:

.. code-block:: python

	two_sprocket_chain = Chain(
	    spkt_teeth = [32, 32],
	    positive_chain_wrap = [True, True],
	    spkt_locations = [ (-5 * IN, 0), (+5 * IN, 0) ]
	)
	relocated_transmission = two_sprocket_chain.assemble_chain_transmission(
	    spkts = [spkt32.cq_object, spkt32.cq_object]
	).rotate(axis=(0,1,1),angle=45).translate((20, 20, 20))

===================
Future Enhancements
===================
Two future enhancements are being considered:

#. Non-planar chains - If the sprocket centers contain ``z`` values, the chain
   would follow the path of a spline between the sockets to approximate the path of
   a bicycle chain where the front and rear sprockets are not in the same plane.
   Currently, the ``z`` values of the first sprocket define the ``z`` offset of the
   entire chain.
#. Sprocket Location Slots - Typically on or more of the
   sprockets in a chain transmission will be adjustable to allow the chain to be
   tight around the sprockets. This could be implemented by allowing the user to
   specify a pair of locations defining a slot for a given sprocket indicating that
   the sprocket location should be selected somewhere along this slot to create a
   perfectly fitting chain.
