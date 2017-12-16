from sqlalchemy import String, Column

from alembic.models.base import BaseBase


class Location(BaseBase):
    """

    """

    #
    address = Column(String(256), nullable=False)

    """
    AddressNumber - address number
    AddressNumberPrefix - a modifier before an address number, e.g. ‘Mile’, ‘#’
    AddressNumberSuffix - a modifier after an address number,
        e.g ‘B’, ‘1/2’
    BuildingName - the name of a building, e.g. ‘Atlanta Financial Center’
    CornerOf - words indicating that an address is a corner,
        e.g. ‘Junction’, ‘corner of’
    IntersectionSeparator - a conjunction connecting parts of an intersection,
        e.g. ‘and’, ‘&’
    LandmarkName - the name of a landmark, e.g. ‘Wrigley Field’, ‘Union Station’
    NotAddress - a non-address component that doesn’t refer to a recipient
    OccupancyType - a type of occupancy within a building,
        e.g. ‘Suite’, ‘Apt’, ‘Floor’
    OccupancyIdentifier - the identifier of an occupancy, often a number or
        letter
    PlaceName - city
    Recipient - a non-address recipient, e.g. the name of a person/organization
    StateName - state
    StreetName - street name, excluding type & direction
    StreetNamePreDirectional - a direction before a street name,
        e.g. ‘North’, ‘S’
    StreetNamePreModifier - a modifier before a street name that is not a
        direction, e.g. ‘Old’
    StreetNamePreType - a street type that comes before a street name,
        e.g. ‘Route’, ‘Ave’
    StreetNamePostDirectional - a direction after a street name,
        e.g. ‘North’, ‘S’
    StreetNamePostModifier - a modifier adter a street name,
        e.g. ‘Ext’
    StreetNamePostType - a street type that comes after a street name,
        e.g. ‘Avenue’, ‘Rd’
    SubaddressIdentifier - the name/identifier of a subaddress component
    SubaddressType - a level of detail in an address that is not an occupancy
        within a building, e.g. ‘Building’, ‘Tower’
    USPSBoxGroupID - the identifier of a USPS box group, usually a number
    USPSBoxGroupType - a name for a group of USPS boxes,
        e.g. ‘RR’
    USPSBoxID - the identifier of a USPS box, usually a number
    USPSBoxType - a USPS box, e.g. ‘P.O. Box’
    ZipCode - zip code
    
    http://www.urisa.org/advocacy/united-states-thoroughfare-landmark-and-postal-address-data-standard/
    """
