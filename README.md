# cq_warehouse

This python/cadquery package contains a set of parametric parts which can
be customized and used within your projects or saved to a CAD file
in STEP or STL format for use in a wide variety of CAD
or CAM systems.

## Table of Contents
- [cq_warehouse](#cq_warehouse)
  - [Table of Contents](#table-of-contents)
  - [Installation](#installation)
  - [Package Structure](#package-structure)
  - [sprocket sub-package](#sprocket-sub-package)
    - [Input Parameters](#input-parameters)
    - [Instance Variables](#instance-variables)
    - [Methods](#methods)
    - [Tooth Tip Shape](#tooth-tip-shape)
  - [chain sub-package](#chain-sub-package)
    - [Input Parameters](#input-parameters-1)
    - [Instance Variables](#instance-variables-1)
    - [Methods](#methods-1)
    - [Future Enhancements](#future-enhancements)
  - [drafting sub-package](#drafting-sub-package)
  - [gear sub-package](#gear-sub-package)
## Installation
Install from github:
```
$ python -m pip install git+https://github.com/gumyr/cq_warehouse.git#egg=cq_warehouse
```
## Package Structure
The cq_warehouse package contains the following sub-packages:
- **sprocket** : a parametric sprocket generator
- **chain**  : a parametric chain generator
- **drafting** : a set of object used for documenting a cadquery object

## sprocket sub-package
A sprocket can be generated and saved to a STEP file with just four lines
of python code using the `Sprocket` class:
```python
import cadquery as cq
from cq_warehouse.sprocket import Sprocket
sprocket32 = Sprocket(32)
cq.exporters.export(sprocket32.cq_object,"sprocket.step")
```
How does this code work?
1. The first line imports cadquery CAD system with the alias cq
2. The second line imports the Sprocket class from the sprocket sub-package of the cq_warehouse package
3. The third line instantiates a 32 tooth sprocket named <q>sprocket32</q>
4. The fourth line uses the cadquery exporter functionality to save the generated
sprocket object in STEP format

Note that instead of exporting sprocket32, sprocket32.cq_object is exported as
sprocket32 contains much more than just the raw CAD object - it contains all of
the parameters used to generate this sprocket - such as the chain pitch - and some
derived information that may be useful - such as the chain pitch radius.

### Input Parameters
Most of the Sprocket parameters are shown in the following diagram:

![sprocket parameters](doc/sprocket_dimensions.png)

The full set of Sprocket input parameters are as follows:
- `num_teeth` (int) : the number of teeth on the perimeter of the sprocket (must be >= 3)
- `chain_pitch` (float) : the distance between the centers of two adjacent rollers - default 1/2" - (pitch in the diagram)
- `roller_diameter` (float) : the size of the cylindrical rollers within the chain - default 5/16" - (roller in the diagram)
- `clearance` (float) : the size of the gap between the chain's rollers and the sprocket's teeth - default 0.0
- `thickness` (float) : the thickness of the sprocket - default 0.084"
- `bolt_circle_diameter` (float) : the diameter of the mounting bolt hole pattern - default 0.0 - (bcd in the diagram)
- `num_mount_bolts` (int) : the number of bolt holes - default 0 - if 0, no bolt holes are added to the sprocket
- `mount_bolt_diameter` (float) : the size of the bolt holes use to mount the sprocket - default 0.0 - (bolt in the diagram)
- `bore_diameter` (float) : the size of the central hole in the sprocket - default 0.0 - if 0, no bore hole is added to the sprocket (bore in the diagram)

---
**NOTE**
Default parameters are for standard single sprocket bicycle chains.

---
The sprocket in the diagram was generated as follows:
```python
MM = 1
chain_ring = Sprocket(
    num_teeth = 32,
    clearance = 0.1*MM,
    bolt_circle_diameter = 104*MM,
    num_mount_bolts = 4,
    mount_bolt_diameter = 10*MM,
    bore_diameter = 80*MM
)
```
---
**NOTE**
Units in cadquery are defined so that 1 represents one millimeter but `MM = 1` makes this
explicit.

---
### Instance Variables
In addition to all of the input parameters that are stored as instance variables
within the Sprocket instance there are four derived instance variables:
- `pitch_radius` (float) : the radius of the circle formed by the center of the chain rollers
- `outer_radius` (float) : the size of the sprocket from center to tip of the teeth
- `pitch_circumference` (float) : the circumference of the sprocket at the pitch rad
- `cq_object` (cq.Workplane) : the cadquery sprocket object

### Methods
The Sprocket class defines two static methods that may be of use when designing with
systems with sprockets: calculation of the pitch radius and pitch circumference as follows:
```python
@staticmethod
def sprocket_pitch_radius(num_teeth:int, chain_pitch:float) -> float:
    """
    Calculate and return the pitch radius of a sprocket with the given number of teeth
    and chain pitch

    Parameters
    ----------
    num_teeth : int
        the number of teeth on the perimeter of the sprocket
    chain_pitch : float
        the distance between two adjacent pins in a single link (default 1/2 INCH)
    """

@staticmethod
def sprocket_circumference(num_teeth:int, chain_pitch:float) -> float:
    """
    Calculate and return the pitch circumference of a sprocket with the given number of
    teeth and chain pitch

    Parameters
    ----------
    num_teeth : int
        the number of teeth on the perimeter of the sprocket
    chain_pitch : float
        the distance between two adjacent pins in a single link (default 1/2 INCH)
    """
```
### Tooth Tip Shape
Normally the tip of a sprocket tooth has a circular section spanning the roller pin sockets
on either side of the tooth tip. In this case, the tip is chamfered to allow the chain to
easily slide over the tooth tip thus reducing the chances of derailing the chain in normal
operation. However, it is valid to generate a sprocket without this <q>flat</q> section by
increasing the size of the rollers. In this case, the tooth tips will be <q>spiky</q> and
will not be chamfered.
## chain sub-package
A chain wrapped around a set of sprockets can be generated with the `Chain` class by providing
the size and locations of the sprockets, how the chain wraps and optionally the chain parameters.

For example, one can create the chain for a bicycle with a rear deraileur as follows:
```python
derailleur_chain = Chain(
    spkt_teeth=[32,10,10,16],
    positive_chain_wrap=[True,True,False,True],
    spkt_locations=[
        (0,158.9*MM,50*MM),
        (+190*MM,0,50*MM),
        (+190*MM,78.9*MM,50*MM),
        (+205*MM,158.9*MM,50*MM)
    ]
)
```
### Input Parameters
The complete set of inputs parameters are:
- `spkt_teeth` (list of int) : a list of the number of teeth on each sprocket the chain will wrap around
- `spkt_locations` (list of cq.Vector or tuple(x,y) or tuple(x,y,z)) : the location of the sprocket centers
- `positive_chain_wrap` (list of bool) : the direction chain wraps around the sprockets, True for counter clock wise viewed from positive Z
- `chain_pitch` (float) : the distance between two adjacent pins in a single link - default 1/2"
- `roller_diameter` (float) : the size of the cylindrical rollers within the chain - default 5/16"
- `roller_length` (float) : the distance between the inner links, i.e. the length of the link rollers - default 3/32"
- `link_plate_thickness` (float) : the thickness of the link plates (both inner and outer link plates) - default 1mm

The chain is created on the XY plane (methods to move the chain are described below)
with the sprocket centers being described by:
- a two dimensional tuple (x,y)
- a three dimensional tuple (x,y,z) which will result in the chain being created parallel
to the XY plane, offset by <q>z</q>
- the cadquery Vector class which will displace the chain by Vector.z

To control the path of the chain between the sprockets, the user must indicate the desired
direction for the chain to wrap around the sprocket. This is done with the `positive_chain_wrap`
parameter which is a list of boolean values - one for each sprocket - indicating a counter
clock wise or positive angle around the z-axis when viewed from the positive side of the XY
plane. The following diagram illustrates the most complex chain path where the chain
traverses wraps from positive to positive, positive to negative, negative to positive and
negative to negative directions (`positive_chain_wrap` values are shown within the arrows
starting from the largest sprocket):

![chain direction](doc/chain_direction.png)

Note that the chain is perfectly tight as it wraps around the sprockets and
does not support any slack. Therefore, as the chain wraps back around to the
first link it will either overlap or gap this link - this can be seen in the above
figure at the top of the largest sprocket. To control this,
the length of the chain in links is echoed to the console window and should
have a small fractional value.  For example, 72.0037 is the value resulting
from the default customizer values which results in a near perfect fit.  A
value of 72.7 would result in a noticeable gap. Adjust the locations of the
sprockets to control this value.

### Instance Variables
In addition to all of the input parameters that are stored as instance variables
within the Chain instance there are seven derived instance variables:
- `pitch_radii` (list of float) : the radius of the circle formed by the center of the chain rollers on each sprocket
- `chain_links` (float) : the length of the chain in links
- `num_rollers` (int) : the number of link rollers in the entire chain
- `roller_loc` (list of cq.Vector) : the location of each roller in the chain
- `chain_angles` (list of tuple(float,float)) : the chain entry and exit angles in degrees for each sprocket
- `spkt_initial_rotation` (list of float) : angle in degrees to rotate each sprocket in-order to align the teeth with the gaps in the chain
- `cq_object` (cq.Assembly) : the cadquery chain object

### Methods
The Chain class defines two methods:
- a static method used to generate chain links cadquery objects, and
- an instance method that will build a cadquery assembly for a chain given a set of sprocket
cadquery objects.
Note that the make_link instance method uses the @cache decorator to greatly improve the rate at
links can be generated as a chain is composed of many copies of the links.

```python
def assemble_chain_transmission(self,spkts:list[Union[cq.Solid,cq.Workplane]]) -> cq.Assembly:
    """
    Create the transmission assembly from sprockets for a chain

    Parameters
    ----------
    spkts : list of cq.Solid or cq:Workplane
        the sprocket cadquery objects to combine with the chain to build a transmission
    """

@staticmethod
@cache
def make_link(
        chain_pitch:float = 0.5*INCH,
        link_plate_thickness:float = 1*MM,
        inner:bool = True,
        roller_length:float = (3/32)*INCH,
        roller_diameter:float = (5/16)*INCH
    ) -> cq.Workplane:
    """
    Create either inner or outer link pairs.  Inner links include rollers while
    outer links include fake roller pins.

    Parameters
    ----------
    chain_pitch : float = (1/2)*INCH
        # the distance between the centers of two adjacent rollers
    link_plate_thickness : float = 1*MM
        # the thickness of the plates which compose the chain links
    inner : bool = True
        # inner links include rollers while outer links include roller pins
    roller_length : float = (3/32)*INCH,
        # the spacing between the inner link plates
    roller_diameter : float = (5/16)*INCH
        # the size of the cylindrical rollers within the chain
    """
```
In addition to the Chain methods, two additional methods are added to the cq.Assembly class
which allow easy manipulation of the resulting chain cadquery objects, as follows:
```python
cq.Assembly.translate(self, vec: VectorLike):
    """
    Moves the current assembly (without making a copy) by the specified translation vector

    Parameters
    ----------
    vec : cq.Vector or tuple(x,y) or tuple(x,y,z)
        The translation vector
    """

cq.Assembly.rotate(self, axis: VectorLike, angle: float):
    """
    Rotates the current assembly (without making a copy) around the axis of rotation
    by the specified angle

    Parameters
    ----------
    axis : cq.Vector or tuple(x,y,z)
        The axis of rotation (starting at the origin)
    angle : float
        the rotation angle, in degrees
    """
```
Once a chain or complete transmission has been generated it can be re-oriented as follows:
```python
two_sprocket_chain = Chain(
    spkt_teeth = [32,32],
    positive_chain_wrap = [True,True],
    spkt_locations = [ (-5*INCH,0), (+5*INCH,0) ]
)
relocated_transmission = two_sprocket_chain.assemble_chain_transmission(
    spkts = [spkt32.cq_object,spkt32.cq_object]
).rotate(axis=(0,1,1),angle=45).translate((20,20,20))
```
### Future Enhancements
Two future enchancments are being considered:
1. Non-planar chains - If the sprocket centers contain `z` values, the
chain would follow the path of a spline between the sockets to approximate
the path of a bicycle chain where the front and read sprockets are not
in the same plane. Currently, the `z` values of the first sprocket defind
the `z` offset of the entire chain.
2. Sprocket Location Slots - Typically on or more of the sprockets in a chain
transmission will be adjustable to allow the chain to be tight around the
sprockets. This could be implemented by allowing the user to specify a pair
of locations defining a slot for a given sprocket indicating that the sprocket
location should be selected somewhere along this slot to create a perfectly
fitting chain.
## drafting sub-package
## gear sub-package
