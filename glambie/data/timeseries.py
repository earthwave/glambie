
from dataclasses import dataclass
from decimal import Decimal
from decimal import getcontext

from glambie.const.data_groups import GlambieDataGroup
from glambie.const.regions import RGIRegion
import numpy as np
import pandas as pd

"""
 def __init__(self, data_group: Optional[GlambieDataGroup] = None, region: Optional[RGIRegion] = None,
                 rgi_version: Optional[int] = None, unit: Optional[str] = None,
                 data_filepath: Optional[str] = None, user: Optional[str] = None, user_group: Optional[str] = None,
                 read_data: Optional[bool] = False):
                 """


@dataclass
class TimeseriesData():
    """Class to wrap the actual data contents"""
    dates: np.ndarray
    area: np.ndarray
    changes: np.ndarray
    errors: np.ndarray

    @property
    def min_time(self) -> float:
        return np.min(self.dates)

    @property
    def max_time(self) -> float:
        return np.max(self.dates)

    @property
    def min_change_value(self) -> float:
        finite_list = np.isfinite(self.changes)
        return np.min(self.changes[finite_list])

    @property
    def max_change_value(self) -> float:
        finite_list = np.isfinite(self.changes)
        return np.max(self.changes[finite_list])

    @property
    def temporal_resolution(self) -> float:
        getcontext().prec = 3  # deal with floating point issues
        resolution = (Decimal(self.max_time) - Decimal(self.min_time)) / len(self)
        return float(resolution)

    def __len__(self) -> int:
        return len(self.dates)

    def as_dataframe(self):
        return pd.DataFrame({'dates': self.dates,
                             'changes': self.changes,
                             'errors': self.errors,
                             'area': self.area
                             })


class Timeseries():
    """Class containing a data series and corresponding metadata"""
    is_data_loaded = False

    def __init__(self, user: str = None, user_group: str = None, data_group: GlambieDataGroup = None,
                 rgi_version: int = None, region: RGIRegion = None, unit: str = None,
                 data_filepath: str = None, data: TimeseriesData = None):

        self.user = user
        self.user_group = user_group
        self.data_group = data_group
        self.rgi_version = rgi_version
        self.region = region
        self.unit = unit
        self.data_filepath = data_filepath
        self.data = data
        if self.data is not None:
            self.is_data_loaded = True

    def load_data(self):
        """Reads data into class, either from specified filepath param or object variable
        """
        if self.data_filepath is None:
            raise ValueError("Can not load: file path not set")

        data = pd.read_csv(self.data_filepath)

        self.data = TimeseriesData(dates=np.array(data['start_dates']),
                                   area=np.array(data['area']),
                                   changes=np.array(data['changes']),
                                   errors=np.array(data['errors']))
        self.is_data_loaded = True

    def metadata_as_dataframe(self):
        region = self.region.name if self.region is not None else None
        data_group = self.data_group.name if self.data_group is not None else None
        return pd.DataFrame({'data_group': data_group,
                             'region': region,
                             'user': self.user,
                             'user_group': self.user_group,
                             'rgi_version': self.rgi_version,
                             'unit': self.unit
                             }, index=[0])
