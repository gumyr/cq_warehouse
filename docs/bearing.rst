#############################
bearing - parametric bearings
#############################
Many mechanical designs will contain bearings of some kind. The
bearing sub-package provides a set of classes that
create many different types of parametric bearings.

Holes for the bearings can be created with a :meth:`~extensions_doc.Workplane.pressFitHole`
method which can automatically place the bearing into an Assembly and bore a hole
for an axle if the part is thicker than the bearing.
See :ref:`Press Fit Holes <press fit holes>` for details.

Here is a list of the classes (and fastener types) provided:

* :ref:`Bearing <bearing>` - the base bearing class

  * ``DeepGrooveBallBearing``: SKT

See :ref:`Extending the fastener sub-package <extending>` (these instructions apply
to bearings as well) for guidance on how to easily
add new sizes or entirely new types of bearings.

 The following example creates a variety of different sized bearings:

.. code-block:: python

	import cadquery as cq
	from cq_warehouse.bearing import DeepGrooveBallBearing

	skate_board_bearing = DeepGrooveBallBearing(size="M8-22-7", bearing_type="SKT")

Both metric and imperial sized standard bearings are directly supported by the bearing sub-package
although the majority of the bearings currently implemented are metric.

All of the fastener classes provide a ``cq_object`` instance variable which contains the cadquery
object.

The following sections describe each of the provided classes.

.. _bearing:

*******
Bearing
*******
As the base class of all other bearing classes, all of the bearing classes share the same
interface as follows:

.. autoclass:: bearing.Bearing


Bearing Selection
=================
As there are many classes and types of bearings to select from, the Bearing class provides some methods
that can help find the correct bearing for your application. As a reminder, to find the subclasses of
the Bearing class, use ``__subclasses__()``:

.. py:module:: bearing

.. doctest::

   	>>> Bearing.__subclasses__()
	[<class 'cq_warehouse.bearing.DeepGrooveBallBearing'>, ...]

Here is a summary of the class methods:

.. automethod:: Bearing.types

.. doctest::

	>>> DeepGrooveBallBearing.types()
	{'SKT'}

.. automethod:: Bearing.sizes

.. doctest::

	>>> DeepGrooveBallBearing.sizes("SKT")
	['M4-9-2.5', 'M4-11-4', 'M4-12-4', 'M4-13-5', 'M4-16-5', 'M8-16-4', 'M8-19-6', 'M8-22-7', 'M8-24-8']

.. automethod:: Bearing.select_by_size

.. doctest::

	>>> Bearing.select_by_size("M8-22-7")
	{<class 'cq_warehouse.bearing.DeepGrooveBallBearing'>: ['SKT']}


Derived Bearing Classes
=======================
The following is a list of the current bearing classes derived from the base Bearing class. Also listed is
the type for each of these derived classes where the type refers to a standard that defines the bearing
parameters. All derived bearings inherit the same API as the base Bearing class.

* ``DeepGrooveBallBearing``: SKT

Detailed information about any of the bearing types can be readily found on the internet from manufacture's
websites or from the standard document itself.

.. _press fit holes:

***************
Press Fit Holes
***************
When designing parts with CadQuery a common operation is to place holes appropriate to a specific bearing
into the part. This operation is optimized with cq_warehouse by the following new Workplane method:

* :meth:`.pressFitHole`

Note that this method can place a hole in the part sized and aligned for the bore of the bearing if
an axle is intended to pass through the part.  The ``fit`` parameter determines how much larger this
hole is than the bearing bore.