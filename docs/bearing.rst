#############################
bearing - parametric bearings
#############################
Many mechanical designs will contain bearings of some kind. The
bearing sub-package provides a set of classes that
create many different types of parametric bearings.

Bearings are created as CadQuery Assemblies and with accurate
external dimensions but simplified internal structure to avoid
excess creation time.

Holes for the bearings can be created with a :meth:`~extensions_doc.Workplane.pressFitHole`
method which can automatically place the bearing into an Assembly and bore a hole
for an axle if the part is thicker than the bearing.
See :ref:`Press Fit Holes <press fit holes>` for details.

Here is a list of the classes (and bearing types) provided:

* :ref:`Bearing <bearing>` - the base bearing class
	* ``SingleRowDeepGrooveBallBearing``: SKT
	* ``SingleRowCappedDeepGrooveBallBearing``: SKT
	* ``SingleRowAngularContactBallBearing``: SKT
	* ``SingleRowCylindricalRollerBearing``: SKT
	* ``SingleRowTaperedRollerBearing``: SKT

See :ref:`Extending the fastener sub-package <extending>` (these instructions apply
to bearings as well) for guidance on how to easily
add new sizes or entirely new types of bearings.

 The following example creates a variety of different sized bearings:

.. code-block:: python

	import cadquery as cq
	from cq_warehouse.bearing import SingleRowDeepGrooveBallBearing, SingleRowTaperedRollerBearing

	skate_board_bearing = SingleRowDeepGrooveBallBearing(size="M8-22-7", bearing_type="SKT")
	motocycle_head_bearing = SingleRowTaperedRollerBearing(size="M20-42-15", bearing_type="SKT")

Both metric and imperial sized standard bearings are directly supported by the bearing sub-package
although the majority of the bearings currently implemented are metric.

.. deprecated:: 0.8

	Previous versions of cq_warehouse required the used of a ``cq_object`` instance variable to access
	the CadQuery cad object. Currently all bearing objects are a sub-class of the CadQuery Compound
	object and therefore can be used as any other Compound object without referencing ``cq_object``.
	Future versions of cq_warehouse will remove ``cq_object`` entirely.

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
	[<class 'cq_warehouse.bearing.SingleRowDeepGrooveBallBearing'>, <class 'cq_warehouse.bearing.SingleRowCappedDeepGrooveBallBearing'>, <class 'cq_warehouse.bearing.SingleRowAngularContactBallBearing'>, <class 'cq_warehouse.bearing.SingleRowCylindricalRollerBearing'>, <class 'cq_warehouse.bearing.SingleRowTaperedRollerBearing'>]

Here is a summary of the class methods:

.. automethod:: Bearing.types

.. doctest::

	>>> SingleRowDeepGrooveBallBearing.types()
	{'SKT'}

.. automethod:: Bearing.sizes

.. doctest::

	>>> SingleRowDeepGrooveBallBearing.sizes("SKT")
	['M3-10-4', 'M4-9-2.5', 'M4-11-4', 'M4-12-4', 'M4-13-5', 'M4-16-5', 'M5-11-3', 'M5-13-4', 'M5-16-5', 'M5-19-6', 'M6-13-3.5', 'M6-15-5', 'M6-19-6', 'M7-14-3.5', 'M7-17-5', 'M7-19-6', 'M7-22-7', 'M8-16-4', 'M8-19-6', 'M8-22-7', 'M8-24-8', 'M9-17-4', 'M9-20-6', 'M9-24-7', 'M9-26-8', 'M10-19-5', 'M10-22-6', 'M10-26-8', 'M10-28-8', 'M10-30-9', 'M10-35-11']

.. automethod:: Bearing.select_by_size

.. doctest::

	>>> Bearing.select_by_size("M8-22-7")
	{<class 'cq_warehouse.bearing.SingleRowDeepGrooveBallBearing'>: ['SKT'], <class 'cq_warehouse.bearing.SingleRowCappedDeepGrooveBallBearing'>: ['SKT']}

Derived Bearing Classes
=======================
The following is a list of the current bearing classes derived from the base Bearing class. Also listed is
the type for each of these derived classes where the type refers to a standard that defines the bearing
parameters. All derived bearings inherit the same API as the base Bearing class.

* ``SingleRowDeepGrooveBallBearing``: SKT
* ``SingleRowCappedDeepGrooveBallBearing``: SKT
* ``SingleRowAngularContactBallBearing``: SKT
* ``SingleRowCylindricalRollerBearing``: SKT
* ``SingleRowTaperedRollerBearing``: SKT

Detailed information about any of the bearing types can be readily found on the internet from manufacture's
websites or from the standard document itself.  SKT provides comprehensive information about all types of
rolling bearings in their document:
`Rolling bearings <https://www.skf.com/binaries/pub12/Images/0901d196802809de-Rolling-bearings---17000_1-EN_tcm_12-121486.pdf>`_.

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