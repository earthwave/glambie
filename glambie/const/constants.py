"""
A set of constants used within the glambie software
"""
from enum import Enum

DENSITY_OF_WATER_KG_PER_M3 = 997
DENSITY_OF_ICE_KG_PER_M3 = 850  # Huss et al. (2013)
OCEAN_AREA_IN_KM2 = 3.625e8  # Cogley et al. (2012)


class YearType(Enum):
    GLACIOLOGICAL = "glaciological"
    CALENDAR = "calendar"
