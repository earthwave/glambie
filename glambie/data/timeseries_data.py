
from decimal import Decimal, getcontext
import numpy as np
from typing import Optional


class ChangeTimeseries():
    """Class containing a data series and corresponding metadata
    """
    @property
    def min_time(self) -> float:
        return self._get_min_time()

    @property
    def max_time(self) -> float:
        return self._get_max_time()

    @property
    def min_change(self) -> float:
        finite_list = np.isfinite(self.change)
        return np.min(self.change[finite_list])

    @property
    def max_mass(self) -> float:
        finite_list = np.isfinite(self.change)
        return np.max(self.change[finite_list])

    def __init__(self, dates: np.ndarray, area: np.ndarray,
                 change: np.ndarray, errors: np.ndarray, rgi_version: int, region_id: int, unit: str,
                 user: Optional[str] = None, user_group: Optional[str] = None, data_group: Optional[str] = None):
        # name of user
        self.user = user
        # experiment group
        self.user_group = user_group
        # experiment group (from data files)
        self.data_group = data_group
        # zwally/rignot/generic
        self.rgi_version = rgi_version
        # basin/ice-sheet id
        self.basin_id = region_id
        # unit of timeseries, ie mwe (gravimetry) or m (other)
        self.unit = unit
        # assign data
        self.dates = dates
        self.area = area
        self.change = change
        self.errors = errors

    def temporal_resolution(self) -> float:
        getcontext().prec = 3  # deal with floating point issues
        resolution = (Decimal(self.max_time) - Decimal(self.min_time)) / len(self)
        return float(resolution)

    def _get_min_time(self) -> float:
        return np.min(self.dates)

    def _get_max_time(self) -> float:
        return np.max(self.dates)

    def __len__(self) -> int:
        return len(self.dates)

    def __bool__(self) -> bool:
        return len(self) > 0
