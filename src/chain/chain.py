"""

Parametric Chains

name: chain.py
by:   Gumyr
date: July 9th 2021

desc:

		This python/cadquery code is a parameterized chain generator.  Given an
array of sprockets data and sprocket locations, a chain can be generated that
wraps around the sprockets - counter clockwise (positive_chain_wrap=True) or
clock wise (positive_chain_wrap=False) - meshing with the teeth of the
sprockets.

		Note that the chain is perfectly tight as it wraps around the sprockets and
does not support any slack. Therefore, as the chain wraps back around to the
first link it will either overlap or gap this link. To control this, the length
of the chain in links is echoed to the console window and should have a small
fractional value.  For example, 72.0037 is the value resulting from the default
customizer values which results in a near perfect fit.  A value of 72.7 would
result in a noticeable gap. Adjust the locations of the sprockets to control
this value.

license:

    Copyright 2021 Gumyr

    Licensed under the Apache License, Version 2.0 (the "License");
    you may not use this file except in compliance with the License.
    You may obtain a copy of the License at

        http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS,
    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    See the License for the specific language governing permissions and
    limitations under the License.

"""
from math import sin, asin, cos, pi, radians, degrees, sqrt, atan2, floor, nan
import warnings
from functools import cache
from typing import Union, Tuple
import cadquery as cq

VectorLike = Union[Tuple[float, float], Tuple[float, float, float], cq.Vector]

VERSION=1.0
MM = 1
INCH = 25.4*MM

#
#  =============================== CLASSES ===============================
#
class Chain:
    """
    Create a new chain object as defined by the given parameters. The input parameter
    defaults are appropriate for a standard bicycle chain.

    Usage:
        c = Chain([32,32],[(-300,0),(300,0)],[True,True])
        print(c.spkt_initial_rotation)       # [5.625, 193.82627377380086]
        c.cq_object.save('chain.step')          # save the cadquery assembly as a STEP file

    Attributes
    ----------
    spkt_teeth : list of int
        a list of the number of teeth on each sprocket the chain will wrap around
    spkt_locations : list of cq.Vector or tuple(x,y) or tuple(x,y,z)
        the location of the sprocket centers
    positive_chain_wrap : list Boolean
        the direction chain wraps around the sprockets, True for counter clock wise viewed
        from positive Z
    chain_pitch : float
        the distance between two adjacent pins in a single link (default 1/2 INCH)
    roller_diameter : float
        the size of the cylindrical rollers within the chain (default 5/16 INCH)
    roller_length : float
        the distance between the inner links, i.e. the length of the link rollers
    link_plate_thickness : float
        the thickness of the link plates (both inner and outer link plates)
    pitch_radii : list of float
        the radius of the circle formed by the center of the chain rollers on each sprocket
    chain_links : float
        the length of the chain in links
    num_rollers : int
        the number of link rollers in the entire chain
    roller_loc : list[cq.Vector]
        the location of each roller in the chain
    chain_angles : list[(float,float)]
        the chain entry and exit angles in degrees for each sprocket
    spkt_initial_rotation : list of float
        a in degrees to rotate each sprocket in-order to align the teeth with the gaps
		in the chain
    cq_object : cadquery.Assembly
        the cadquery chain object

    Methods
    -------

    assemble_chain_transmission(spkts:list[cq.Solid or cq.Workplane],chain:Chain) -> cq.Assembly:
        Create a cq.Assembly from an array of sprockets and a chain object

    make_link(chain_pitch:float,link_plate_thickness:float,inner:bool,roller_length:float,
        roller_diameter:float) -> cq.Workplane:
        Create either an internal or external chain link as a cq.Workplane object

    """
    # pylint: disable=dangerous-default-value
    # The dangerous-default-value refers to the list arguments with defaults which are
    # not a problem for two reasons. Firstly, these arguments are never assigned a
    # value within this class potentially changing the default. Secondly, these
    # arguments are in the __init__ method and therefore only used once.
    def __init__(self,
            spkt_teeth:list[int] = [32,32],
            spkt_locations:list[VectorLike] = [(-5*INCH,0,0),(+5*INCH,0,0)],
            positive_chain_wrap:list[bool] = [True,True],
            chain_pitch:float = (1/2)*INCH,
            roller_diameter:float = (5/16)*INCH,
            roller_length:float = (3/32)*INCH,
            link_plate_thickness:float = 1.0*MM
        ):
        """
        Create a new chain assembly object as defined by the given parameters centered on
				the XY plane.  The input parameter defaults are appropriate for a standard bicycle
				chain.

        Parameters
        ----------
        spkt_teeth : list of int
            a list of the number of teeth on each sprocket the chain will wrap around
        spkt_locations : list of cq.Vector or tuple(x,y) or tuple(x,y,z)
            the location of the sprocket centers
        positive_chain_wrap : list of bool
            the direction chain passes over the sprockets, True for counter clock wise viewed
            from positive Z
        chain_pitch : float
            the distance between two adjacent pins in a single link (default 1/2 INCH)
        roller_diameter : float
            the size of the cylindrical rollers within the chain (default 5/16 INCH)
        roller_length : float
            the distance between the inner links, i.e. the length of the link rollers
        link_plate_thickness : float
            the thickness of the link plates (both inner and outer link plates)
        """

        # Parameter parsing
        self.spkt_teeth = spkt_teeth
        if not isinstance(self.spkt_teeth,list) or \
           not all(isinstance(i, int) for i in self.spkt_teeth) or \
           len(self.spkt_teeth)<2:
            raise  TypeError("spkt_teeth must be a list of multiple integers")
        _num_spkts = len(self.spkt_teeth)
        self.spkt_locations = spkt_locations
        if not isinstance(self.spkt_locations,list) or \
           not all(isinstance(i, (cq.Vector,tuple)) for i in self.spkt_locations):
            raise TypeError("spkt_locations must be a list of cq.Vector")
        # pylint: disable=no-member
        _spkt_locs = [ cq.Vector(l.x,l.y,0)
            if isinstance(l,cq.Vector) else cq.Vector(l[0],l[1],0)
            for l in self.spkt_locations
        ]
        if isinstance(spkt_locations[0],cq.Vector):
            _plane_offset = spkt_locations[0].z
        else:
            _plane_offset = spkt_locations[0][2] if len(spkt_locations[0])==3 else 0
        if len({ loc.toTuple() for loc in _spkt_locs })!=_num_spkts:
            raise ValueError("At least two sprockets are in the same location")
        self.positive_chain_wrap = positive_chain_wrap
        if not isinstance(self.positive_chain_wrap,list) or \
           not all(isinstance(i, bool) for i in self.positive_chain_wrap):
            raise TypeError("positive_chain_wrap must be a list of boolean")
        if not len(self.spkt_teeth)==len(self.spkt_locations)==len(self.positive_chain_wrap):
            raise ValueError("Length of spkt_teeth, spkt_locations, positive_chain_wrap not equal")
        self.chain_pitch = chain_pitch
        self.roller_diameter = roller_diameter
        if roller_diameter >= chain_pitch:
            raise ValueError("roller_diameter {} is too large for chain_pitch {}" \
                .format(roller_diameter,chain_pitch))
        self.roller_length = roller_length
        self.link_plate_thickness = link_plate_thickness
        self.pitch_radii = [
            Sprocket.sprocket_pitch_radius(t,self.chain_pitch)
            for t in self.spkt_teeth
        ]

        # Calculate the distance between sprocket centers
        _spkt_sep = [
            (_spkt_locs[(s+1)%_num_spkts] - _spkt_locs[s]).Length
            for s in range(_num_spkts)
        ]

        # Calculate the distance the chain spans between two sprockets
        _line_l = [
            sqrt(pow(_spkt_sep[s],2) -
                 pow(self.pitch_radii[s] - self.pitch_radii[(s+1)%_num_spkts],2))
            if self.positive_chain_wrap[s]==self.positive_chain_wrap[(s+1)%_num_spkts]
            else
                sqrt(pow(_spkt_sep[s],2) -
                     pow(self.pitch_radii[s] + self.pitch_radii[(s+1)%_num_spkts],2))
            for s in range(_num_spkts)
        ]

        #
        # Calculate the angle that the chain enters and departs the sprockets
        # 1- determine the angle between the sprocket centers
        # 2- determine the extra angle resulting from different sized sprockets:
		    #    asin((Rn+Rn-1)/separation)
        # 3- based on the relative rotational direction of the two sprockets,
        #    determine the angle the chain will exit the first sprocket
        _base_a = [
            90+degrees(atan2(_spkt_locs[s].y-_spkt_locs[(s+1)%_num_spkts].y,
						     _spkt_locs[s].x-_spkt_locs[(s+1)%_num_spkts].x))
            for s in range(_num_spkts)
        ]

        _exit_a = []
        for s in range(_num_spkts):
            if self.positive_chain_wrap[s] and \
			   self.positive_chain_wrap[(s+1)%_num_spkts]:
                _exit_a.append(_base_a[s]-90 +
								degrees(asin((self.pitch_radii[s] -
							  self.pitch_radii[(s+1)%_num_spkts])/_spkt_sep[s])))
            elif self.positive_chain_wrap[s] and \
                 not self.positive_chain_wrap[(s+1)%_num_spkts]:
                _exit_a.append(_base_a[s]-90 +
                            degrees(asin((self.pitch_radii[s] +
                            self.pitch_radii[(s+1)%_num_spkts])/_spkt_sep[s])))
            elif not self.positive_chain_wrap[s] and \
                 self.positive_chain_wrap[(s+1)%_num_spkts]:
                _exit_a.append(_base_a[s]+90-degrees(asin((self.pitch_radii[s]+
								self.pitch_radii[(s+1)%_num_spkts])/_spkt_sep[s])))
            else:
                _exit_a.append(_base_a[s]+90-degrees(asin((self.pitch_radii[s]-
								self.pitch_radii[(s+1)%_num_spkts])/_spkt_sep[s])))

        # The entry a of a sprocket is the same the exit a of the previous sprocket
        _entry_a = [
            _exit_a[(s-1)%_num_spkts]+180
            if self.positive_chain_wrap[s]!=self.positive_chain_wrap[(s-1)%_num_spkts]
            else
                _exit_a[(s-1)%_num_spkts]
            for s in range(_num_spkts)
        ]

        # Record the entry and exit angles as tuples per sprocket
        self.chain_angles = [*zip(_entry_a,_exit_a)]

        # Calculate the length of the arc where the chain is in contact with the sprocket
        _arc_a = [
            (_exit_a[s]-_entry_a[s]+360)%360
            if self.positive_chain_wrap[s]
            else
                (_entry_a[s]-_exit_a[s]+360)%360
            for s in range(_num_spkts)
        ]
        _arc_l =  [
            abs(_arc_a[s]*2*pi*self.pitch_radii[s]/360)
            for s in range(_num_spkts)
        ]

        # Calculate the 2D point where the chain enters and exits the sprockets
        _spkt_entry_exit_loc = [
            [_spkt_locs[s]+cq.Vector(0,self.pitch_radii[s]).rotateZ(_entry_a[s]),
             _spkt_locs[s]+cq.Vector(0,self.pitch_radii[s]).rotateZ(_exit_a[s])]
            for s in range(_num_spkts)
        ]
        # Generate a list of all the chain segment lengths [arc,line,arc,...]
        _segment_lengths = Chain._interleave_lists(_arc_l,_line_l)

        # Generate a list of the sum of the chain segment lengths [arc,line,arc,...]
        _segment_sums = Chain._gen_mix_sum_list(_arc_l,_line_l)

        # The chain length is the last of the segment sums
        _chain_length = _segment_sums[-1]

        # Length of the chain in links
        self.chain_links = _chain_length/self.chain_pitch

        # Round to the nearest number of rollers - note, should be close to ..
        # .. an integer to avoid gaps in the chain and positioning errors
        self.num_rollers = floor(_chain_length/self.chain_pitch)

        # Determine the location of all the chain rollers
        self.roller_loc = []
        _roller_a_per_spkt = []
        for i in range(self.num_rollers):
            _roller_distance = (i*self.chain_pitch)%_chain_length
            _roller_segment = Chain._find_segment(_roller_distance,_segment_sums)
            _roller_spkt = floor(_roller_segment/2)
            _along_segment = 1-(_segment_sums[_roller_segment]-
                _roller_distance)/_segment_lengths[_roller_segment]
            if _roller_segment%2==0 and  self.positive_chain_wrap[_roller_spkt]:
                _roller_a = _entry_a[_roller_spkt] + \
                _arc_a[_roller_spkt]*_along_segment
            elif _roller_segment%2==0 and not self.positive_chain_wrap[_roller_spkt]:
                _roller_a = _entry_a[_roller_spkt] - \
                _arc_a[_roller_spkt]*_along_segment
            else:
                _roller_a = nan

            if _roller_segment%2==0:       # on a sprocket
                self.roller_loc.append(_spkt_locs[_roller_spkt] +
                    cq.Vector(0,self.pitch_radii[_roller_spkt]).rotateZ(_roller_a))
            else:                               # between two sprockets
                self.roller_loc.append(
                    (_spkt_entry_exit_loc[(_roller_spkt+1)%_num_spkts][0]-
                    _spkt_entry_exit_loc[_roller_spkt][1])*_along_segment +
                    _spkt_entry_exit_loc[_roller_spkt][1]
                )
            # For the rollers that are in contact with a sprocket, record their angles
            if _roller_segment%2==0:
                _roller_a_per_spkt.append([_roller_spkt,_roller_a])

        # Filter the roller as to just the first one per sprocket
        _first_roller_a_per_spkt = [
            _roller_a_per_spkt[[_roller_a_per_spkt[i][0]
            for i in range(len(_roller_a_per_spkt))].index(s)][1]
            for s in range(_num_spkts)
        ]
        #
        # Calculate the angle to rotate the sprockets such that the teeth are between the rollers
        self.spkt_initial_rotation = [
            _first_roller_a_per_spkt[s]+180/self.spkt_teeth[s]
            for s in range(_num_spkts)
        ]
        #
        # Warn the user if the length in links creates a gap
        # (The user needs to repositioning the ..
        # .. sprockets to achieve a near integer number of links)
        if self.chain_links-floor(self.chain_links)>0.5:
            warnings.warn(message="Chain has missing links",category=Warning)

        #
        # ----------- Now that the link locations have be determined, assemble the chain -----------

        #
        # Initialize the chain assembly
        self.cq_object = cq.Assembly(None,name="chain_links")

        #
        # Add the links to the chain assembly
        for i in range(self.num_rollers):
            # Calculate the bend in the chain at each roller
            _link_rotation_a_d = degrees(
                atan2(self.roller_loc[(i+1)%self.num_rollers].y-self.roller_loc[i].y,
                self.roller_loc[(i+1)%self.num_rollers].x-self.roller_loc[i].x)
            )
            _link_location = cq.Location(self.roller_loc[i].pointToVector('XY',_plane_offset))
            self.cq_object.add(
                Chain.make_link(inner=i%2==0).rotate((0,0,0),cq.Vector(0,0,1),_link_rotation_a_d),
                name="link"+str(i),
                loc=_link_location
            )

    def assemble_chain_transmission(self,spkts:list[Union[cq.Solid,cq.Workplane]]) -> cq.Assembly:
        """
        Create the transmission assembly from sprockets for a chain
        """
        if not isinstance(spkts,list) or \
           not all(isinstance(i, (cq.Solid, cq.Workplane)) for i in spkts):
            raise TypeError("spkts must be a list of cadquery Solid or Workplane")

        transmission = cq.Assembly(None,name="transmission")

        for spkt_num,spkt in enumerate(spkts):
            spktname = "spkt"+str(spkt_num)
            transmission.add(
                spkt
                .rotate((0,0,0),(0,0,1),self.spkt_initial_rotation[spkt_num])
                .translate(self.spkt_locations[spkt_num]),
                name=spktname
            )
        transmission.add(self.cq_object, name="chain")
        return transmission

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
        """

        def link_plates(chain_pitch,thickness,inner=False):
            """ Create a single chain link, either inner or outer """
            plate_scale = chain_pitch/(0.5*INCH)
            neck = plate_scale*4.5*MM/2
            plate_r = plate_scale*8.5*MM/2
            neck_r = (pow(chain_pitch/2,2)+pow(neck,2)-pow(plate_r,2))/(2*plate_r-2*neck)
            plate_cen_pt = cq.Vector(chain_pitch/2,0)
            plate_neck_intersection_a = degrees(atan2(neck+neck_r,chain_pitch/2))
            neck_tangent_pt=cq.Vector(plate_r,0).rotateZ(180-plate_neck_intersection_a)+plate_cen_pt

            # Create a dog boned link plate
            plate = (cq.Workplane("XY")
                .hLine(chain_pitch/2+plate_r,forConstruction=True)
                .threePointArc((chain_pitch/2,plate_r),neck_tangent_pt.toTuple())
                .radiusArc((0,neck),neck_r)
                .mirrorX()
                .mirrorY()
                .extrude(thickness/2,both=True)
                )
            # Add roller pins
            if not inner:
                plate = (plate.faces(">Z").workplane().tag("Outside")
                        .center(-chain_pitch/2, 0).circle(plate_r/4).extrude(thickness/3)
                        .workplaneFromTagged("Outside")
                        .center(+chain_pitch/2, 0).circle(plate_r/4).extrude(thickness/3))
            return plate

        def roller(roller_diameter = (5/16)*INCH,roller_length=(3/32)*INCH):
            roller=(cq.Workplane("XY").circle(roller_diameter/2).extrude(roller_length/2,both=True))
            return roller

        if inner:
            # Link Plates
            link = (link_plates(chain_pitch,link_plate_thickness,inner=True)
                .translate((chain_pitch/2,0,(roller_length+link_plate_thickness)/2.0))
            )
            link = link.union(
                (link_plates(chain_pitch,link_plate_thickness,inner=True)
                    .translate((chain_pitch/2,0,-(roller_length+link_plate_thickness)/2))
                )
            )
            # Link Rollers
            link = link.union(roller(roller_diameter,roller_length))
            link = link.union(roller(roller_diameter,roller_length).translate((chain_pitch,0,0)))
        else:
            link = (link_plates(chain_pitch,link_plate_thickness,inner=False)
                .translate((chain_pitch/2,0,(roller_length+3*link_plate_thickness)/2))
            )
            link = link.union(
                (link_plates(chain_pitch,link_plate_thickness,inner=False)
                    .translate((chain_pitch/2,0,(roller_length+3*link_plate_thickness)/2))
                    .rotate((0,0,0),(1,0,0),180)
                )
            )

        return link

    @staticmethod
    def _gen_mix_sum_list(list_a:list,list_b:list) -> list:
        """
        Return the sum the values of two interleaving arrays
        print(_gen_mix_sum_list([1,2,3,4],[3,4,1,2]))  #  [1, 4, 6, 10, 13, 14, 18, 20]
        """
        if len(list_a)!=len(list_b):
            raise ValueError("_gen_mix_sum_list require two lists of equal size")
        array_sum = [list_a[0],list_a[0]+list_b[0]]
        for i in range(1,len(list_a)):
            array_sum.append(array_sum[-1]+list_a[i])
            array_sum.append(array_sum[-1]+list_b[i])
        return array_sum

    @staticmethod
    def _interleave_lists(list_a:list,list_b:list) -> list:
        """
        Return a single interleaved array given two equal sized lists
        print(_interleave_lists([1,2,3,4],[3,4,1,2]))  #  [1, 3, 2, 4, 3, 1, 4, 2]
        """
        if len(list_a)!=len(list_b):
            raise ValueError("_interleave_lists require two lists of equal size")
        return_list = [None]*2*len(list_a)     # Create an empty list of the correct size
        return_list[::2] = list_a              # Assign a to the even-numbered indices
        return_list[1::2] = list_b             # Assign b to the odd-numbered indices
        return return_list

    @staticmethod
    def _find_segment(len_value:float,len_array:list[float]) -> int:
        """
        Return a position in a length array given a length value
        """
        return_value = nan
        for i,len_array_value in enumerate(len_array):
            if len_value < len_array_value:
                return_value = i
                break
        return return_value

#
#  =============================== FUNCTIONS BOUND TO OTHER CLASSES ===============================
#
def _translate(self, vec: VectorLike):
    """
    Moves the current assembly (without making a copy) by the specified translation vector
    :param vec: The translation vector
    """
    self.loc = self.loc*cq.Location(cq.Vector(vec))
    return self
cq.Assembly.translate = _translate

def _rotate(self, axis: VectorLike, angle: float):
    """
    Rotates the current assembly (without making a copy) around the axis of rotation
    by the specified angle

    :param axis: The axis of rotation (starting at the origin)
    :type axis: a 3-tuple of floats
    :param angle: the rotation angle, in degrees
    :type angle: float
    """
    self.loc = self.loc*cq.Location(cq.Vector(0,0,0),cq.Vector(axis),angle)
    return self
cq.Assembly.rotate = _rotate
