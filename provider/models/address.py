from sqlalchemy import Column, String, Integer

from provider.models.base import Base


class Address(Base):
    """
    The address components are based upon the United States Thoroughfare,
    Landmark, and Postal Address Data Standard, and usaddress knows about the
    following types of components:

    http://www.urisa.org/advocacy/united-states-thoroughfare-landmark-and
    -postal-address-data-standard/
    """

    # Address number
    address_number = Column(String(16))

    # AddressNumberPrefix - a modifier before an address number, e.g. ‘Mile’,‘#’
    address_number_prefix = Column(String())

    # AddressNumberSuffix - a modifier after an address number, e.g ‘B’, ‘1/2’
    address_number_suffix = Column(String(8))

    # BuildingName - the name of a building, e.g. ‘Atlanta Financial Center’
    building_name = Column(String())

    # CornerOf - words indicating that an address is a corner,
    #     e.g. ‘Junction’, ‘corner of’
    corner_of = Column(String())

    # IntersectionSeparator - a conjunction connecting parts of an intersection,
    #     e.g. ‘and’, ‘&’
    intersection_separator = Column(String(8))

    # LandmarkName - the name of a landmark, e.g. ‘Wrigley Field’, ‘Union
    # Station’
    landmark_name = Column(String(64))

    # NotAddress - a non-address component that doesn’t refer to a recipient
    not_address = Column(String())

    # OccupancyType - a type of occupancy within a building,
    #     e.g. ‘Suite’, ‘Apt’, ‘Floor’
    occupancy_type = Column(String(16))

    # OccupancyIdentifier - the identifier of an occupancy, often a number or
    #     letter
    occupancy_identifier = Column(String(32))

    # PlaceName - city
    place_name = Column(String(64))

    # Recipient - a non-address recipient, e.g. the name of a person/org
    recipient = Column(String(128))

    # StateName - state
    # TODO: ENUM
    state_name = Column(String(32))

    # StreetName - street name, excluding type & direction
    street_name = Column(String(64))

    # StreetNamePreDirectional - a direction before a street name,
    #     e.g. ‘North’, ‘S’
    street_name_pre_directional = Column(String(16))

    # StreetNamePreModifier - a modifier before a street name that is not a
    #     direction, e.g. ‘Old’
    street_name_pre_modifier = Column(String(8))

    # StreetNamePreType - a street type that comes before a street name,
    #     e.g. ‘Route’, ‘Ave’
    street_name_pre_type = Column(String(16))

    # StreetNamePostDirectional - a direction after a street name,
    #     e.g. ‘North’, ‘S’
    street_name_post_directional = Column(String(16))

    # StreetNamePostModifier - a modifier adter a street name,
    #     e.g. ‘Ext’
    street_name_post_modifier = Column(String(8))

    # StreetNamePostType - a street type that comes after a street name,
    #     e.g. ‘Avenue’, ‘Rd’
    street_name_post_type = Column(String(32))

    # SubaddressIdentifier - the name/identifier of a subaddress component
    subaddress_identifier = Column(String(16))

    # SubaddressType - a level of detail in an address that is not an occupancy
    #     within a building, e.g. ‘Building’, ‘Tower’
    subaddress_type = Column(String(16))

    # USPSBoxGroupID - the identifier of a USPS box group, usually a number
    usps_box_group_id = Column(String())

    # USPSBoxGroupType - a name for a group of USPS boxes,
    #     e.g. ‘RR’
    usps_box_group_type = Column(String())

    # USPSBoxID - the identifier of a USPS box, usually a number
    # TODO: Always a number?
    usps_box_id = Column(String(8))

    # USPSBoxType - a USPS box, e.g. ‘P.O. Box’
    # TODO: Enum
    usps_box_type = Column(String(8))

    # ZipCode - zip code
    zip_code = Column(Integer())

    # ZipCodePlusFour - zip+4
    zip_code_plus_four = Column(Integer())
