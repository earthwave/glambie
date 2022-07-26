
from decimal import Decimal
from decimal import getcontext
from typing import Optional

from glambie.const.data_groups import GlambieDataGroup
from glambie.const.regions import RGIRegion
import numpy as np
import pandas as pd


class ChangeTimeseries():
    """Class containing a data series and corresponding metadata
    """
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

    def __init__(self, data_group: Optional[GlambieDataGroup] = None, region: Optional[RGIRegion] = None,
                 rgi_version: Optional[int] = None, unit: Optional[str] = None,
                 data_filepath: Optional[str] = None, user: Optional[str] = None, user_group: Optional[str] = None,
                 read_data: Optional[bool] = False):
        # name of user
        self.user = user
        # experiment group
        self.user_group = user_group
        # experiment group (from data files)
        self.data_group = data_group
        # rgi
        self.rgi_version = rgi_version
        # basin
        self.region = region
        # unit of timeseries, ie mwe (gravimetry) or m (other)
        self.unit = unit
        # filepath of data
        self.data_filepath = data_filepath
        if read_data and self.data_filepath is not None:
            self.read_data()

    def read_data(self, data_filepath: Optional[str] = None):
        """Reads data into class, either from specified filepath param or object variable
        """
        if data_filepath is not None:
            self.data_filepath = data_filepath

        data = pd.read_csv(self.data_filepath)
        self.ingest_data(dates=np.array(data['start_dates']),
                         area=np.array(data['area']),
                         changes=np.array(data['changes']),
                         errors=np.array(data['errors']),
                         )

    def ingest_data(self, dates: np.ndarray, area: np.ndarray,
                    changes: np.ndarray, errors: np.ndarray):
        # assign data
        self.dates = dates
        self.area = area
        self.changes = changes
        self.errors = errors

    def temporal_resolution(self) -> float:
        getcontext().prec = 3  # deal with floating point issues
        resolution = (Decimal(self.max_time) - Decimal(self.min_time)) / len(self)
        return float(resolution)

    def data_as_dataframe(self):
        return pd.DataFrame({'dates': self.dates,
                             'changes': self.changes,
                             'errors': self.errors,
                             'area': self.area
                             })

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

    def __len__(self) -> int:
        return len(self.dates)

    def __bool__(self) -> bool:
        return len(self) > 0
