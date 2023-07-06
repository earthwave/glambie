
from __future__ import annotations

import copy
from dataclasses import dataclass
from decimal import Decimal
from decimal import getcontext
import warnings

from glambie.const.data_groups import GlambieDataGroup
from glambie.const.regions import RGIRegion
from glambie.data.submission_system_interface import fetch_timeseries_dataframe, SUBMISSION_SYSTEM_FLAG
from glambie.util.mass_height_conversions import \
    meters_to_meters_water_equivalent
from glambie.util.mass_height_conversions import \
    meters_water_equivalent_to_gigatonnes
from glambie.util.timeseries_helpers import derivative_to_cumulative, get_total_trend
from glambie.util.timeseries_helpers import \
    resample_derivative_timeseries_to_monthly_grid
from glambie.util.timeseries_helpers import timeseries_as_months
from glambie.util.timeseries_helpers import timeseries_is_monthly_grid
from glambie.util.timeseries_helpers import get_average_trends_over_new_time_periods
from glambie.util.date_helpers import get_years
from glambie.util.timeseries_combination_helpers import calibrate_timeseries_with_trends
from glambie.util.timeseries_combination_helpers import combine_calibrated_timeseries
from glambie.const import constants
from glambie.const.density_uncertainty import get_density_uncertainty_over_survey_period


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
    start_dates: np.ndarray  # start date of change observed.
    end_dates: np.ndarray  # end date of change observed.
    changes: np.ndarray  # change observed between start and end date.
    errors: np.ndarray  # errors of observed change.
    # Area of region taken from a reference glacier mask: e.g. Randolph Glacier Inventory v6.0 or v7.0.
    glacier_area_reference: np.ndarray
    # Area of region supplied alongside the timeseries data, a measurement made by the data provider.
    glacier_area_observed: np.ndarray
    hydrological_correction_value: np.ndarray  # A correction value used specifically for gravimetry.
    remarks: np.ndarray  # An extra column for per-timeseries string comments.

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
        return pd.DataFrame({
            'start_dates': self.start_dates,
            'end_dates': self.end_dates,
            'changes': self.changes,
            'errors': self.errors,
            'glacier_area_reference': self.glacier_area_reference,
            'glacier_area_observed': self.glacier_area_observed,
            'hydrological_correction_value': (
                self.hydrological_correction_value
                if self.hydrological_correction_value is not None
                else np.full(len(self.changes), None)),
            'remarks': (
                self.remarks
                if self.remarks is not None
                else np.full(len(self.changes), None)),
        })

    def as_cumulative_timeseries(self) -> pd.DataFrame:
        """
        Calculates the cumulative timeseries

        Returns
        -------
        pd.DataFrame
            Dataframe containing the cumulative changes
            Instead of start_dates and end_dates, the column 'dates' is used
        """
        if not self.is_cumulative_valid():
            warnings.warn("Cumulative timeseries may be invalid. This may be due to the timeseries containing "
                          "gaps or overlapping periods.")
        dates, changes = derivative_to_cumulative(self.start_dates, self.end_dates, self.changes)
        errors = np.array([0, *self.errors])  # need to handle errors in the future too
        df_cumulative = pd.DataFrame({'dates': dates,
                                      'changes': changes,
                                      'errors': errors
                                      })
        return df_cumulative

    def is_cumulative_valid(self):
        """
        Checks if computing a cumulative time series will be valid or not.
        The conditions for validity are:
        - No gaps in timeseries (i.e. for each end date there must be another start date, except for the last one)
        - No overalapping spans

        Returns
        -------
        boolean
            True if valid, False if not valid
        """
        return all(start_date == end_date for start_date, end_date in zip(self.start_dates[1:], self.end_dates[:-1]))


class Timeseries():
    """Class containing a data series and corresponding metadata
    """
    is_data_loaded = False

    def __init__(self, region: RGIRegion = None, data_group: GlambieDataGroup = None, data_filepath: str = None,
                 data: TimeseriesData = None, user: str = None, user_group: str = None,
                 rgi_version: int = None, unit: str = None, additional_metadata: dict = None):
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
            unit the timeseries is in, e.g. m, mwe or gt, by default None
        additional_metadata : dict, optional
            additional metadata fields collected by the submission system, but not directly used within the study.
        """
        self.user = user
        self.user_group = user_group
        self.data_group = data_group
        self.rgi_version = rgi_version
        self.region = region
        self.unit = unit
        self.data_filepath = data_filepath
        self.data = data
        self.additional_metadata = additional_metadata
        if self.data is not None:
            self.is_data_loaded = True

    def load_data(self) -> TimeseriesData:
        """Reads data into class from specified filepath
        """
        if self.data_filepath is None:
            raise ValueError("Can not load data: file path not set")
        elif self.data_filepath == SUBMISSION_SYSTEM_FLAG:
            data = fetch_timeseries_dataframe(self.user_group, self.region, self.data_group)
        else:
            data = pd.read_csv(self.data_filepath)

        self.data = TimeseriesData(
            start_dates=np.array(data['start_date_fractional']),
            end_dates=np.array(data['end_date_fractional']),
            changes=np.array(data['glacier_change_observed']),
            errors=np.array(data['glacier_change_uncertainty']),
            glacier_area_reference=np.array(data['glacier_area_reference']),
            glacier_area_observed=np.array(data['glacier_area_observed']),
            hydrological_correction_value=(
                np.array(data['hydrological_correction_value'])
                if 'hydrological_correction_value' in data.columns else None),
            remarks=(
                np.array(data['remarks'])
                if 'remarks' in data.columns else None))
        self.is_data_loaded = True
        return self.data

    def metadata_as_dataframe(self) -> pd.DataFrame:
        """
        Returns meta data for a timeseries dataset as a dataframe.

        Returns
        -------
        pd.DataFrame
            Dataframe containing dataset meta data
        """
        metadata_dict = {
            'data_group': getattr(self.data_group, 'name', None),
            'region': getattr(self.region, 'name', None),
            'user': self.user,
            'user_group': self.user_group,
            'rgi_version': self.rgi_version,
            'unit': self.unit
        }
        if self.additional_metadata is not None:
            metadata_dict.update(self.additional_metadata)
        return pd.DataFrame(metadata_dict, index=[0])

    def timeseries_is_monthly_grid(self):
        """
        Returns True if all values in the self.data.start_dates and self.data.end_dates are on
        the monthly grid defined by glambie.util.timeseries_helpers.timeseries_as_months.
        Also returns True if the resolution is not monthly, but all dates are using the monthly grid.

        Returns
        -------
        bool
            True if in monthly grid, False otherwise.
        """
        return timeseries_is_monthly_grid(self.data.start_dates) and timeseries_is_monthly_grid(self.data.end_dates)

    def timeseries_is_annual_grid(self, year_type: constants.YearType = constants.YearType.CALENDAR):
        """
        Returns True if all values in the self.data.start_dates and self.data.end_dates are on
        the annual grid (e.g. 2010.0 would be on annual calendar year grid, 2010.1 would not)
        Also returns Trues if the resolution is not annual, but all dates are using the annual grid.

        Parameters
        ----------
        year_type : constants.YearType, optional
            annual grid to which the timeseries will be homogenized to, options are 'calendar', 'glaciological'
            by default "calendar"

        Returns
        -------
        bool
            True if in annual grid, False otherwise.
        """
        if year_type == constants.YearType.CALENDAR:
            year_start = 0
        elif year_type == constants.YearType.GLACIOLOGICAL:
            year_start = self.region.glaciological_year_start

        return all(s % 1 == year_start for s in self.data.start_dates) and all(s % 1 == year_start
                                                                               for s in self.data.end_dates)

    def copy(self) -> Timeseries:
        """
        Returns a deep copy of itself

        Returns
        -------
        Timeseries
            a copy of itself
        """
        return copy.deepcopy(self)

    def convert_timeseries_to_unit_mwe(self, density_of_water: float = constants.DENSITY_OF_WATER_KG_PER_M3,
                                       density_of_ice: float = constants.DENSITY_OF_ICE_KG_PER_M3) -> Timeseries:
        """
        Converts a Timeseries object to the unit of meters water equivalent.
        Errors are calculated using different density uncertainties depending on time resolution of timeseries.
        Returns a copy of itself with the converted glacier changes.

        Parameters
        ----------
        density_of_water: float, optional
            The density of water in Gt per m3, by default constants.DENSITY_OF_WATER_KG_PER_M3
        density_of_ice : float, optional
            The density of ice in Gt per m3, by default constants.DENSITY_OF_ICE_KG_PER_M3

        Returns
        -------
        Timeseries
            A copy of the Timeseries object containing the converted timeseries data and corrected metadata information.

        Raises
        ------
        NotImplementedError
            For units to be converted that are not implemented yet
        """
        if self.unit == "mwe":  # no conversion needed as already in mwe
            return self.copy()
        else:
            object_copy = self.copy()
            object_copy.unit = "mwe"
            if self.unit == "m":
                object_copy.data.changes = np.array(meters_to_meters_water_equivalent(object_copy.data.changes,
                                                                                      density_of_water=density_of_water,
                                                                                      density_of_ice=density_of_ice))
                # Uncertainties
                # First, convert elevation change error in m to mwe
                object_copy.data.errors = np.array(meters_to_meters_water_equivalent(object_copy.data.errors,
                                                                                     density_of_water=density_of_water,
                                                                                     density_of_ice=density_of_ice))
                # Second, include density uncertainty in error
                density_unc = get_density_uncertainty_over_survey_period(self.data.max_temporal_resolution)
                df = object_copy.data.as_dataframe()
                # also see formula in Glambie Assessment Algorithm document, section 5.2 Homogenization of data
                errors_mwe = df.changes.abs() * ((df.errors / df.changes)**2 + (density_unc / density_of_ice)**2)**0.5
                object_copy.data.errors = np.array(errors_mwe)
                return object_copy
            else:
                raise NotImplementedError(
                    "Conversion to mwe not implemented yet for Timeseries with unit '{}'".format(self.unit))

    def convert_timeseries_to_unit_gt(self, density_of_water: float = constants.DENSITY_OF_WATER_KG_PER_M3,
                                      rgi_area_version=6) -> Timeseries:
        """
        Converts a Timeseries object to the unit of Gigatonnes.
        Returns a copy of itself with the converted glacier changes.

        Parameters
        ----------
        density_of_water: float, optional
            The density of water in Gt per m3, by default constants.DENSITY_OF_WATER_KG_PER_M3
        rgi_area_version: int, optional
            The version of RGI glacier masks to be used to determine the glacier area within the region,
            Current options are 6 or 7, by default 6

        Returns
        -------
        Timeseries
            A copy of the Timeseries object containing the converted timeseries data and corrected metadata information.

        Raises
        ------
        NotImplementedError
            For units to be converted that are not implemented yet
        """
        # get area
        if rgi_area_version == 6:
            glacier_area = self.region.rgi6_area
        elif rgi_area_version == 7:
            glacier_area = self.region.rgi7_area
        else:
            raise NotImplementedError("Version '{}' of RGI is not implemented yet.".format(rgi_area_version))

        object_copy = self.copy()
        object_copy.unit = "gt"

        if self.unit == "gt":  # no conversion needed as already in gt
            return self.copy()
        elif self.unit == "mwe":
            object_copy.data.changes = np.array(meters_water_equivalent_to_gigatonnes(
                self.data.changes, area_km2=glacier_area, density_of_water=density_of_water))
            # variables for uncertainty calculation
            # area_unc is calculated as a % of the total area. % can be defined individually per region.
            area_unc = glacier_area * self.region.area_uncertainty_percentage  # use individual glacier area unc
            area = glacier_area

            # Uncertainties
            # First, convert elevation change uncertaintiesr in mwe to Gt
            object_copy.data.errors = np.array(meters_water_equivalent_to_gigatonnes(
                self.data.errors, area_km2=glacier_area, density_of_water=density_of_water))
            # Second, include area uncertainty in uncertainty
            df = object_copy.data.as_dataframe()
            # also see formula in Glambie Assessment Algorithm document, section 5.2 Homogenization of data
            uncertainties_gt = df.changes.abs() * ((df.errors / df.changes)**2 + (area_unc / area)**2)**0.5
            object_copy.data.errors = np.array(uncertainties_gt)
            return object_copy

        else:
            raise NotImplementedError(
                "Conversion to Gt not implemented yet for Timeseries with unit '{}'".format(self.unit))

    def apply_area_change(self, rgi_area_version: int = 6, apply_change: bool = True) -> Timeseries:
        """
        Applies or removes a changing area to observed changes.
        Returns a copy of itself with the converted timeseries.

        Parameters
        ----------
        rgi_area_version : int, optional
            version of RGI used for area change, by default 6
        apply_change : bool, optional
            Describes if the area change should be applied or removed
            If set to False, the area change is removed rather than applied, by default True

        Returns
        -------
        Timeseries
            A copy of the Timeseries object containing the converted timeseries data.

        """
        if self.unit not in ["mwe", "m"]:
            raise AssertionError("Area change should only applied to 'm' or 'mwe'.")
        # get area
        if rgi_area_version == 6:
            glacier_area = self.region.rgi6_area
        elif rgi_area_version == 7:
            glacier_area = self.region.rgi7_area

        object_copy = self.copy()
        # conversion with area change
        area_chnage_reference_year = self.region.area_change_reference_year
        area_change = self.region.area_change
        adjusted_changes = []
        adjusted_areas = []

        df = self.data.as_dataframe()
        for start_date, end_date, change in zip(df["start_dates"], df["end_dates"], df["changes"]):
            t_i = (start_date + end_date) / 2
            adjusted_area = glacier_area + (t_i - area_chnage_reference_year) * (area_change / 100) * glacier_area
            if apply_change:
                adjusted_changes.append(glacier_area / adjusted_area * change)
            else:  # remove change
                adjusted_changes.append(change / (glacier_area / adjusted_area))
            adjusted_areas.append(adjusted_area)
        object_copy.data.changes = np.array(adjusted_changes)
        return object_copy

    def convert_timeseries_to_monthly_grid(self) -> Timeseries:
        """
        Converts a Timeseries object to follow the monthly grid. Two different approaches are used depending on
        time resolution of the timeseries:

        1.) Resolution over half a year: Timeseries is shifted to the closest month within the monthly grid
            This method cannot be applied for monthly resolution as it may lead to empty months.
        2.) Resolution under half a year: Timeseries is resampled to the monthly grid

        Returns
        -------
        Timeseries
            A copy of the Timeseries object containing the converted timeseries data to the monthly grid.
        """
        # make a deep copy of itself
        object_copy = self.copy()
        if not self.timeseries_is_monthly_grid():  # if already in monthly grid there is no need to convert
            # check resolution
            if self.data.max_temporal_resolution >= 0.5:  # resolution above half a year: shift to closest month
                start_dates = timeseries_as_months(self.data.start_dates, downsample_to_month=False)
                end_dates = timeseries_as_months(self.data.end_dates, downsample_to_month=False)
                object_copy.data.start_dates = np.array(start_dates)
                object_copy.data.end_dates = np.array(end_dates)
            else:  # resolution below half a year: resample timeseries to monthly grid
                start_dates, end_dates, changes = resample_derivative_timeseries_to_monthly_grid(self.data.start_dates,
                                                                                                 self.data.end_dates,
                                                                                                 self.data.changes)
                # resample uncertainties
                _, _, errors = resample_derivative_timeseries_to_monthly_grid(self.data.start_dates,
                                                                              self.data.end_dates,
                                                                              self.data.errors)

                object_copy.data = TimeseriesData(start_dates=np.array(start_dates),
                                                  end_dates=np.array(end_dates),
                                                  changes=np.array(changes),
                                                  errors=np.array(errors),
                                                  glacier_area_observed=None,
                                                  glacier_area_reference=None,
                                                  hydrological_correction_value=None,
                                                  remarks=None)

        return object_copy  # return copy of itself

    def convert_timeseries_to_annual_trends(self,
                                            year_type: constants.YearType = constants.YearType.CALENDAR) -> Timeseries:
        """
        Converts a timeseries to annual trends. Note that this assumes that the timeseries is already using the annual
        grid for resolutions >= 1 year and the monthly grid for resolutions <= 1 year.

        Parameters
        ----------
        year_type : constants.YearType, optional
            annual grid to which the timeseries will be homogenized to, options are 'calendar', 'glaciological'
            by default "calendar"

        Returns
        -------
        Timeseries
            A copy of the Timeseries object containing the converted timeseries data to annual trends.

        Raises
        ------
        AssertionError
            Thrown if timeseries is not on monthly grid.
        AssertionError
            Thrown for resolutions > 1 year if timeseries is not on annual grid.
        """
        # Check if on monthly grid. if not throw an exception
        if not self.timeseries_is_monthly_grid():
            raise AssertionError("Timeseries needs to be converted to monthly grid before performing this operation.")

        if year_type == constants.YearType.CALENDAR:
            year_start = 0
        elif year_type == constants.YearType.GLACIOLOGICAL:
            year_start = self.region.glaciological_year_start

        object_copy = self.copy()

        # 1) Case where resolution is < 1 year: we upsample and take the average from e.g. all the months within a year
        if self.data.max_temporal_resolution <= 1:  # resolution higher than a year
            min_date, max_date = np.array(self.data.start_dates).min(), np.array(self.data.end_dates).max()
            new_start_dates, new_end_dates = get_years(year_start, min_date=min_date,
                                                       max_date=max_date, return_type="arrays")
            df_annual = get_average_trends_over_new_time_periods(start_dates=self.data.start_dates,
                                                                 end_dates=self.data.end_dates,
                                                                 changes=self.data.changes,
                                                                 new_start_dates=new_start_dates,
                                                                 new_end_dates=new_end_dates)
            df_annual_errors = get_average_trends_over_new_time_periods(start_dates=self.data.start_dates,
                                                                        end_dates=self.data.end_dates,
                                                                        changes=self.data.errors,
                                                                        new_start_dates=new_start_dates,
                                                                        new_end_dates=new_end_dates,
                                                                        calculate_as_errors=True)
            object_copy.data.start_dates = np.array(df_annual["start_dates"])
            object_copy.data.end_dates = np.array(df_annual["end_dates"])
            object_copy.data.changes = np.array(df_annual["changes"])
            object_copy.data.errors = np.array(df_annual_errors["changes"])
            object_copy.data.glacier_area_observed = None
            object_copy.data.glacier_area_reference = None

        # 2) Case where resolution is >= a year: we upsample and take the average from the longterm trend
        else:  # make sure that the trends don't start in the middle of the year
            if not self.timeseries_is_annual_grid(year_type=year_type):
                raise AssertionError("Timeseries needs be at to fit into annual grid before \
                                     up-sampling to annual changes.")
            new_start_dates, new_end_dates = get_years(year_start, min_date=self.data.start_dates.min(),
                                                       max_date=self.data.end_dates.max(), return_type="arrays")
            new_changes = []
            new_uncertainties = []
            for _, row in self.data.as_dataframe().iterrows():
                time_period = row["end_dates"] - row["start_dates"]
                annual_trend = row["changes"] / time_period
                annual_unc = row["errors"] / time_period
                # add annual trend times number of years to the new changes
                new_changes.extend([annual_trend for _ in range(int(time_period))])
                new_uncertainties.extend([annual_unc for _ in range(int(time_period))])
            assert len(new_changes) == len(new_start_dates) == len(new_end_dates)
            object_copy.data.start_dates = np.array(new_start_dates)
            object_copy.data.end_dates = np.array(new_end_dates)
            object_copy.data.changes = np.array(new_changes)
            object_copy.data.errors = np.array(new_uncertainties)
            object_copy.data.glacier_area_observed = None
            object_copy.data.glacier_area_reference = None

        return object_copy  # return copy of itself

    def convert_timeseries_to_longterm_trend(self) -> Timeseries:
        """
        Converts a timeseries to a longterm trend.
        The calculated longterm trend will be the overall trend from min(start_dates) to max(end_dates)).

        Returns
        -------
        Timeseries
            A copy of the Timeseries object containing the converted timeseries data to a longterm trend.
        """
        object_copy = self.copy()
        trend = get_total_trend(self.data.start_dates, self.data.end_dates, self.data.changes, return_type="dataframe")

        trend_errors = get_total_trend(self.data.start_dates, self.data.end_dates,
                                       self.data.errors, return_type="value", calculate_as_errors=True)

        object_copy.data = TimeseriesData(start_dates=np.array(trend["start_dates"]),
                                          end_dates=np.array(trend["end_dates"]),
                                          changes=np.array(trend["changes"]),
                                          errors=np.array([trend_errors]), glacier_area_observed=None,
                                          glacier_area_reference=None,
                                          hydrological_correction_value=None,
                                          remarks=None)

        return object_copy  # return copy of itself

    def convert_timeseries_using_seasonal_homogenization(self, seasonal_calibration_dataset: Timeseries,
                                                         year_type: constants.YearType = constants.YearType.CALENDAR,
                                                         p_value: int = 0) -> Timeseries:
        """
        Converts a timeseries to a specific annual grid using seasonal homogenization.
        A high resolution timeseries with seasonal information is used to 'shift' and correct the current
        timesteps to the desired annual grid (e.g. calendar or glaciological).

        For more information check the Glambie algorithm description document.

        Parameters
        ----------
        seasonal_calibration_dataset : Timeseries
            High resolution dataset to be used for calibration
        year_type : constants.YearType, optional
            annual grid to which the timeseries will be homogenized to, options are 'calendar', 'glaciological'
            by default "calendar"
        p_value : int, optional
            p value for distance weight during seasonal homogenization,
            by default 0, meaning that no distance weight is applied

        Returns
        -------
        Timeseries
            A copy of the Timeseries object containing the converted timeseries data to annual trends.
            The timeseries will have the same temporal resolution as the input timeseries, but will be shifted
            and corrected to the annual grid (which is defined through year_type).

        Raises
        ------
        AssertionError
            Thrown if timeseries is not on monthly grid.
        AssertionError
            Thrown if calibration dataset is not on monthly grid.
        AssertionError
            Thrown if timeseries resolution below a year.
        """
        # first some checks if inputs area valid
        if not self.timeseries_is_monthly_grid():
            raise AssertionError("Timeseries needs to be converted to monthly grid before performing this operation.")
        if not seasonal_calibration_dataset.timeseries_is_monthly_grid():
            raise AssertionError("Seasonal calibration dataset needs to be converted to monthly grid"
                                 "before performing this operation.")
        if self.data.max_temporal_resolution < 1:
            raise AssertionError("Resolution of timeseries is below a year. No seasonal homogenization possible.")
        if not self.unit == seasonal_calibration_dataset.unit:
            raise AssertionError("Seasonal calibration dataset and dataset unit should be the same, however "
                                 f"they are units {seasonal_calibration_dataset.unit} and {self.unit}.")

        if year_type == constants.YearType.CALENDAR:
            year_start = 0
        elif year_type == constants.YearType.GLACIOLOGICAL:
            year_start = self.region.glaciological_year_start

        object_copy = self.copy()
        if not self.timeseries_is_annual_grid(year_type=year_type):  # if already annual then no need to homogenize
            # 1) calibrate calibration series with trends from timeseries
            calibrated_s, dist_mat = calibrate_timeseries_with_trends(self.data.as_dataframe(),
                                                                      seasonal_calibration_dataset.data.as_dataframe())
            # 2) calculate mean calibration timeseries from all the different curves
            mean_calibrated_ts = combine_calibrated_timeseries(calibrated_s, dist_mat, p_value=p_value,
                                                               calculate_outside_calibrated_series_period=True)
            df_mean_calibrated = pd.DataFrame({"start_dates": seasonal_calibration_dataset.data
                                               .as_dataframe().start_dates,
                                               "end_dates": seasonal_calibration_dataset.data
                                              .as_dataframe().end_dates, "changes": mean_calibrated_ts})
            # 3) remove nan values where timeseries didn't cover
            df_mean_calibrated = df_mean_calibrated[~df_mean_calibrated.isna()].reset_index()

            # 4) read out homogenized values
            # get desired annual grid, buffer 2 years to work with start and end dates and include rounded years
            annual_grid = get_years(year_start, min_date=self.data.start_dates.min() - 2,
                                    max_date=self.data.end_dates.max() + 3, return_type="arrays")[0]
            new_start_dates, new_end_dates, new_changes, new_errors = [], [], [], []
            for start_date, end_date, error \
                    in zip(self.data.start_dates, self.data.end_dates, self.data.errors):
                # get dates from annual grid
                new_start_date = annual_grid[np.abs(annual_grid - start_date).argmin()]
                new_end_date = annual_grid[np.abs(annual_grid - end_date).argmin()]
                # read the new changes from the calibrated timeseries
                df_filtered_year = df_mean_calibrated[(df_mean_calibrated.start_dates >= new_start_date)
                                                      & (df_mean_calibrated.end_dates <= new_end_date)]
                # handle case when timeseries is outside the calibration timeseries
                if df_filtered_year.shape[0] == 0:
                    new_change = None
                    new_error = None
                else:  # this case tests if we actually cover the full period or only part of the period
                    if df_filtered_year.start_dates.min() == new_start_date \
                            and df_filtered_year.end_dates.max() == new_end_date:
                        new_change = df_filtered_year["changes"].sum()

                        # CALCULATE ERROR
                        # 1 calculate temporal homogenization error
                        # make cumulative timeseries of calibrated high resolution dataset for start and end balances
                        df_mean_calibrated_cumulative = df_mean_calibrated.copy()
                        df_mean_calibrated_cumulative.changes = df_mean_calibrated.changes.cumsum()
                        df_filtered_year_cum_initial_dates = df_mean_calibrated_cumulative[
                            (df_mean_calibrated_cumulative.start_dates >= start_date)
                            & (df_mean_calibrated_cumulative.end_dates <= end_date)]
                        df_filtered_year_cum_new_dates = df_mean_calibrated_cumulative[
                            (df_mean_calibrated_cumulative.start_dates >= new_start_date)
                            & (df_mean_calibrated_cumulative.end_dates <= new_end_date)]
                        # temporal error is 0.5 * (|delta_B_start_date| + |delta_B_end_date|)
                        # For more info see glambie Assessment Algorithm Document
                        # i.e. the correction at start and end date
                        delta_balance_start = abs(
                            df_filtered_year_cum_initial_dates.changes.iloc[0]
                            - df_filtered_year_cum_new_dates.changes.iloc[0])
                        delta_balance_end = abs(
                            df_filtered_year_cum_initial_dates.changes.iloc[-1]
                            - df_filtered_year_cum_new_dates.changes.iloc[-1])
                        error_temp = 0.5 * (delta_balance_start + delta_balance_end)

                        # 2. combine errors assuming random error propagation
                        new_error = (error**2 + error_temp**2)**0.5

                    else:
                        new_change = None
                        new_error = None

                # Append
                new_changes.append(new_change)
                new_errors.append(new_error)
                new_start_dates.append(float(new_start_date))
                new_end_dates.append(float(new_end_date))

            # apply new arrays to object copy
            object_copy.data.start_dates = np.array(new_start_dates)
            object_copy.data.end_dates = np.array(new_end_dates)
            object_copy.data.changes = np.array(new_changes)
            object_copy.data.errors = np.array(new_errors)

            # remove nan values
            df_nan_removed = object_copy.data.as_dataframe()[~object_copy.data.as_dataframe()["changes"].isna()]
            object_copy.data.start_dates = np.array(df_nan_removed["start_dates"])
            object_copy.data.end_dates = np.array(df_nan_removed["end_dates"])
            object_copy.data.changes = np.array(df_nan_removed["changes"])
            object_copy.data.errors = np.array(df_nan_removed["errors"])
            object_copy.data.glacier_area_observed = np.array(df_nan_removed["glacier_area_observed"])
            object_copy.data.glacier_area_reference = np.array(df_nan_removed["glacier_area_reference"])

        return object_copy
