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


class ExtractTrendsMethod(Enum):
    """
    Describing methods used to extract trends from a higher reolution timeseries
    """
    # fitting a linear regression when extracting a trend from a higher resolution timeseries
    REGRESSION = "regression"
    # calculating end_date minus start_date value when extracting a trend from a higher resolution timeseries
    START_VS_END = "start_vs_end"


class SeasonalCorrectionMethod(Enum):
    """
    Describing methods used to correct long-term trends or annual trends when they are not starting or ending in
    the desired season, i.e. do not follow the desired annual grid
    """
    # using proportional scaling when converting a low resolution (annual or longer) timeseries to the annual grid
    PROPORTIONAL = "proportional"
    # using a high resolution seasonal correction dataset when converting a low resolution (annual or longer)
    # timeseries to the annual grid
    SEASONAL_HOMOGENIZATION = "seasonal_homogenization"


class GraceGap(Enum):
    """
    A class describing the time gap between the two gravimetry missions (GRACE and GRACE-FO).
    """
    START_DATE = 2017.4
    END_DATE = 2018.6
