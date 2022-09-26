
from dataclasses import dataclass
from decimal import Decimal
from decimal import getcontext

from glambie.const.data_groups import GlambieDataGroup
from glambie.const.regions import RGIRegion
import numpy as np
import pandas as pd


@dataclass
class TimeseriesData():
    """Class to wrap the actual data contents of a Timeseries
    The timeseries data are saved containing a start and enddate for each glacier change value.
    The respective glacier change is then the change between start and end date.
    This means, that time series are used as derivatives and not as cumulative timeseries.

    For more information check the GlaMBIE Assessment Framework,
    or the data submission instructions on the GlaMBIE website.
    """
    start_dates: np.ndarray  # start date of change observed
    end_dates: np.ndarray  # end date of change observed
    changes: np.ndarray  # change observed between start and end date
    errors: np.ndarray  # errors of observed change
    # Area of region taken from a reference glacier mask: e.g. Randolph Glacier Inventory v6.0 or v7.0.
    glacier_area_reference: np.ndarray
    # Area of region supplied alongside the timeseries data, a measurement made by the data provider.
    glacier_area_observed: np.ndarray

    @property
    def min_start_date(self) -> float:
        return np.min(self.start_dates)

    @property
    def max_start_date(self) -> float:
        return np.max(self.start_dates)

    @property
    def min_end_date(self) -> float:
        return np.min(self.end_dates)

    @property
    def max_end_date(self) -> float:
        return np.max(self.end_dates)

    @property
    def min_change_value(self) -> float:
        finite_list = np.isfinite(self.changes)
        return np.min(self.changes[finite_list])

    @property
    def max_change_value(self) -> float:
        finite_list = np.isfinite(self.changes)
        return np.max(self.changes[finite_list])

    @property
    def min_temporal_resolution(self) -> float:
        getcontext().prec = 3  # deal with floating point issues
        resolution = np.max([Decimal(end) - Decimal(start) for end, start in zip(self.end_dates, self.start_dates)])
        return float(resolution)

    @property
    def max_temporal_resolution(self) -> float:
        getcontext().prec = 3  # deal with floating point issues
        resolution = np.min([Decimal(end) - Decimal(start) for end, start in zip(self.end_dates, self.start_dates)])
        return float(resolution)

    def __len__(self) -> int:
        return len(self.dates)

    def as_dataframe(self):
        return pd.DataFrame({'start_dates': self.start_dates,
                            'end_dates': self.end_dates,
                             'changes': self.changes,
                             'errors': self.errors,
                             'glacier_area_reference': self.glacier_area_reference,
                             'glacier_area_observed': self.glacier_area_observed
                             })


class Timeseries():
    """Class containing a data series and corresponding metadata
    """
    is_data_loaded = False

    def __init__(self, region: RGIRegion = None, data_group: GlambieDataGroup = None, data_filepath: str = None,
                 data: TimeseriesData = None, user: str = None, user_group: str = None,
                 rgi_version: int = None, unit: str = None):
        """
        Class containing meta data and data from of an individual timeseries.

        Follows either lazy loading of data files OR direct data ingestion on object creation:
            - If only filename is specified, data will not be ingested immediately,
            it can be loaded later from the datafile with load_data()
            - If data (TimeseriesData object) is specified on object creation, the data is ingested immediately

        Parameters
        ----------
        region : RGIRegion, optional
            region if timeseres, by default None
        data_group : GlambieDataGroup, optional
            data group, e.g. if it's altimetry or gravimetry, by default None
        data_filepath : str, optional
            full file path to csv, if data is not specified it can later be read with this filepath, by default None
        data : TimeseriesData, optional
            The actual data contents of a Timeseries, by default None
        user : str, optional
            name of user / participant, by default None
        user_group : str, optional
            name of participant group, by default None
        rgi_version : int, optional
            which version of rgi has been used, e.g. 6 or 7, by default None
        unit : str, optional
            unit the timeseries is in, e.g. m or mwe, by default None
        """
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

    def load_data(self) -> TimeseriesData:
        """Reads data into class from specified filepath
        """
        if self.data_filepath is None:
            raise ValueError("Can not load data: file path not set")

        data = pd.read_csv(self.data_filepath)

        self.data = TimeseriesData(start_dates=np.array(data['start_date_fractional']),
                                   end_dates=np.array(data['end_date_fractional']),
                                   changes=np.array(data['glacier_change_observed']),
                                   errors=np.array(data['glacier_change_uncertainty']),
                                   glacier_area_reference=np.array(data['glacier_area_reference']),
                                   glacier_area_observed=np.array(data['glacier_area_observed']))
        self.is_data_loaded = True
        return self.data

    def metadata_as_dataframe(self) -> pd.DataFrame:
        """
        Returns meta data for a timeseries dataset as a dataframe

        Returns
        -------
        pd.DataFrame
            Dataframe containing dataset meta data
        """
        region = self.region.name if self.region is not None else None
        data_group = self.data_group.name if self.data_group is not None else None
        return pd.DataFrame({'data_group': data_group,
                             'region': region,
                             'user': self.user,
                             'user_group': self.user_group,
                             'rgi_version': self.rgi_version,
                             'unit': self.unit
                             }, index=[0])
