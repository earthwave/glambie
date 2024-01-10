from __future__ import annotations

import json
import os
from typing import Tuple
import warnings

from glambie.const.data_groups import GLAMBIE_DATA_GROUPS, GlambieDataGroup
from glambie.const.regions import REGIONS, REGIONS_BY_SHORT_NAME
from glambie.const.regions import RGIRegion
from glambie.data.timeseries import Timeseries, TimeseriesData
from glambie.data.submission_system_interface import (
    fetch_all_submission_metadata, fetch_timeseries_dataframe, SUBMISSION_SYSTEM_BASEPATH_PLACEHOLDER)
import pandas as pd
import numpy as np
import copy


class DataCatalogue():
    """Class containing a catalogue of datasets
    """

    def __init__(self, base_path: str, datasets: list[Timeseries]):
        self._base_path = base_path
        self._datasets = datasets

    @staticmethod
    def from_glambie_submission_system() -> DataCatalogue:
        """
        Loads a catalogue from the GlaMBIE submission system.

        Where a submission does not have an RGI Version
        (because we introduced this requirement partway through the process), we substitute 6.0.

        To get the unit, we need to load the file and check.

        Returns
        -------
        DataCatalogue
            Data catalogue (actually all of the data, not just metadata) containing data for GlaMBIE.
        """
        submission_system_metadata = fetch_all_submission_metadata()

        datasets = []
        for metadata in submission_system_metadata:
            # create a reduced dict that only contains the metadata fields that this repo does not directly use.
            additional_metadata = {
                k: v for k, v in metadata.items() if k not in [
                    'region', 'observational_source', 'lead_author_name', 'user_group', 'rgi_version_select']}

            datasets.append(
                Timeseries(
                    region=REGIONS_BY_SHORT_NAME[metadata['region'].upper()],
                    data_group=GLAMBIE_DATA_GROUPS[
                        metadata['observational_source'].replace('dem_differencing', 'demdiff')],
                    data_filepath=SUBMISSION_SYSTEM_BASEPATH_PLACEHOLDER,
                    user=metadata['lead_author_name'],
                    user_group=metadata['user_group'],
                    rgi_version=metadata.get('rgi_version_select', '6.0'),
                    additional_metadata=additional_metadata))

            # we need to load the data anyway to get the unit, so may as well keep it loaded.
            data = fetch_timeseries_dataframe(
                datasets[-1].user_group, datasets[-1].region, datasets[-1].data_group)
            datasets[-1].unit = data['unit'].iloc[0]
            datasets[-1].data = TimeseriesData(
                start_dates=np.array(data['start_date_fractional']),
                end_dates=np.array(data['end_date_fractional']),
                changes=np.array(data['glacier_change_observed']),
                errors=np.array(data['glacier_change_uncertainty']),
                glacier_area_reference=np.array(data['glacier_area_reference']),
                glacier_area_observed=np.array(data['glacier_area_observed']),
                hydrological_correction_value=(
                    np.array(data['hydrological_correction_value'])
                    if 'hydrological_correction_value' in data.columns else None),
                remarks=np.array(data['remarks']))

        return DataCatalogue(SUBMISSION_SYSTEM_BASEPATH_PLACEHOLDER, datasets)

    @staticmethod
    def from_json_file(metadata_file_path: str) -> DataCatalogue:
        """
        Loads a catalogue from a json file

        Parameters
        ----------
        metadata_file_path : str
            full file path to json metadata catalogue file

        Returns
        -------
        DataCatalogue
            Data Catalogue for GlaMBIE.
            The data will be lazily loaded into the catalogue as required, gradually turning it into a full database.
        """
        with open(metadata_file_path) as json_file:
            return DataCatalogue.from_dict(json.load(json_file))

    @staticmethod
    def from_dict(meta_data_dict: dict) -> DataCatalogue:
        """
        Loads a catalogue from a dictionnary

        Parameters
        ----------
        meta_data_dict : dict
            dictionary of catalogue metadata

        Returns
        -------
        DataCatalogue
            Data Catalogue for GlaMBIE.
            The data will be lazily loaded into the catalogue as required, gradually turning it into a full database.
        """
        base_path = os.path.join(*meta_data_dict['base_path'])
        datasets_dict = meta_data_dict['datasets']
        datasets = []
        for ds_dict in datasets_dict:
            fp = os.path.join(base_path, ds_dict['filename'])
            region = REGIONS[ds_dict['region']]
            data_group = GLAMBIE_DATA_GROUPS[ds_dict['data_group']]
            user_group = ds_dict['user_group']
            unit = ds_dict['unit']
            datasets.append(Timeseries(data_filepath=fp, region=region, data_group=data_group, user_group=user_group,
                                       unit=unit))

        return DataCatalogue(base_path, datasets)

    @staticmethod
    def from_list(datasets_list: list[Timeseries], base_path: str = "") -> DataCatalogue:
        """
        Loads a catalogue from a list of Timeseries datasets

        Parameters
        ----------
        datasets_list : list
            list of Timeseries objects
        base_path : str
            basepath for loading the actual data, default is an empty string ''
            Note that if the data is already loaded there is no need to set this parameter.

        Returns
        -------
        DataCatalogue
            Data Catalogue for GlaMBIE.
            The data will be lazily loaded into the catalogue as required, gradually turning it into a full database.
        """
        return DataCatalogue(base_path, datasets_list)

    @property
    def datasets(self) -> list[Timeseries]:
        return self._datasets

    @property
    def regions(self) -> list[RGIRegion]:
        return list({s.region for s in self._datasets})  # get as a set, so only unique values

    @property
    def base_path(self) -> str:
        return self._base_path

    def as_dataframe(self) -> pd.DataFrame:
        metadata_list = [ds.metadata_as_dataframe() for ds in self._datasets]
        return pd.concat(metadata_list)

    def get_filtered_catalogue(self, region_name: str = None, data_group: str = None,
                               user_group: str = None) -> DataCatalogue:
        """
        Returns a catalogue filtered by region name, data group or user group

        Parameters
        ----------
        region_name : str, optional
            region to filter by, by default None
        data_group : str, optional
            data group to filter by, by default None
        user_group : str, optional
            user group to filter by, by default None

        Returns
        -------
        DataCatalogue
            A filtered version of the input catalogue
        """
        datasets = self._datasets
        if region_name is not None:  # filter by region
            datasets = [s for s in datasets if s.region.name.lower() == region_name.lower()]
        if data_group is not None:  # filter by data group
            datasets = [s for s in datasets if s.data_group.name.lower() == data_group.lower()]
        if user_group is not None:  # filter by user group
            datasets = [s for s in datasets if s.user_group.lower() == user_group.lower()]
        return self.__class__(self.base_path, datasets)

    def copy(self):
        """
        Copy the catalogue

        Returns
        -------
        DataCatalogue
            Deep copy of itslef
        """
        return copy.deepcopy(self)

    def load_all_data(self):
        """
        Loads the timeseries data of all datasets in catalogue
        Only loads data if it is not already loaded in a specific dataset
        """
        for dataset in self.datasets:
            if not dataset.is_data_loaded:
                dataset.load_data()

    def datasets_are_same_unit(self):
        """
        Checks if all datasets within catalogue have the same unit

        Returns
        -------
        bool
            True if all dataset units are the same, False otherwise
        """
        if len(self.datasets) > 0:
            unit = self.datasets[0].unit
            return all(dataset.unit == unit for dataset in self.datasets)
        else:
            return True

    def get_time_span_of_datasets(self) -> Tuple[float, float]:
        """
        Returns the time window covered by all datasets within the catalogue

        Returns
        -------
        Tuple[float, float]
            minimum and maximum dates of all datasets combined in catalogue
            in the form of [min_start_date, max_end_date]
        """
        if len(self.datasets) > 0:
            min_dates = []
            max_dates = []

            for ds in self.datasets:
                min_dates.append(ds.data.min_start_date)
                max_dates.append(ds.data.max_end_date)
            return np.min(min_dates), np.max(max_dates)
        else:
            return None, None

    def average_timeseries_in_catalogue(self, remove_trend: bool = True, add_trend_after_averaging: bool = False,
                                        out_data_group: GlambieDataGroup = GLAMBIE_DATA_GROUPS["consensus"],
                                        out_user_group: str = "consensus") \
            -> Tuple[Timeseries, DataCatalogue]:
        """
        Calculates a simple average of all timeseries within the catalogue, with the option to remove trends
        and calculate the average on the anomalies

        Parameters
        ----------
        remove_trend : bool, optional
            if set to True, the trend over a shared time period is removed, by default True
        add_trend_after_averaging : bool, optional
            this will add the average trends from all the input solutions in the catalogue to the averaged solution
            this flag is only active when remove_trend is set to True.
            by default False
        out_data_group : GlambieDataGroup, optional
            data group to be assigned to combined output Timeseries metadata
            by default GLAMBIE_DATA_GROUPS["consensus"]
        out_user_group : str, optional
            user group to be assigned to combined output Timeseries metadata
            by default 'consensus'


        Returns
        -------
        Tuple[Timeseries, DataCatalogue]
            1. Timeseries object, containing the new combined solution
            2. DataCatalogue, containing the catalogue the operation was performed on.
               For remove_trend set to False, this is an exact copy of self.
               For remove_trend set to True, this contains the altered datasets with the trends removed

        Raises
        ------
        AssertionError
            If timeseries within catalogue are not all the same unit.
        """

        if not self.datasets_are_same_unit():
            raise AssertionError("Timeseries within catalogue need to be same unit before performing this operation.")

        # merge all dataframes
        catalogue_dfs = [ds.data.as_dataframe() for ds in self.datasets]

        data_catalogue_out = self.copy()  # DataCatalogue object for returning

        # remove trend / calculate beta instead of B
        if remove_trend:
            change_means_over_period = []  # keep track for adding back in case add_trend_after_averaging=True
            start_ref_period = np.max([df.start_dates.min() for df in catalogue_dfs])
            end_ref_period = np.min([df.end_dates.max() for df in catalogue_dfs])

            if not start_ref_period < end_ref_period:
                warnings.warn("Warning when removing trends. No common period detected.")
            for idx, df in enumerate(catalogue_dfs):
                df_sub = df[(df["start_dates"] >= start_ref_period) & (df["end_dates"] <= end_ref_period)]
                df["changes"] = df["changes"] - df_sub["changes"].mean()
                data_catalogue_out.datasets[idx].data.changes = np.array(df["changes"])
                change_means_over_period.append(df_sub["changes"].mean())

        # join all catalogues by start and end dates
        # the resulting dataframe has a set of columns with repeating prefixes
        df_merged = pd.concat([x.set_index(['start_dates', 'end_dates']) for x in catalogue_dfs],
                              axis=1, keys=range(len(catalogue_dfs)))
        df_merged.columns = df_merged.columns.map('{0[1]}_{0[0]}'.format)
        df_merged = df_merged.sort_values(by="start_dates")
        df_merged = df_merged.reset_index()
        start_dates, end_dates = np.array(df_merged["start_dates"]), np.array(df_merged["end_dates"])
        mean_changes = np.array(df_merged[df_merged.columns.intersection(
            df_merged.filter(regex=("changes_*")).columns.to_list())].mean(axis=1))

        # UNCERTAINTIES -- more information is in GlaMBIE Assessment Algorithm document
        # 1 ) propagate observational uncertainties
        sigma_obs_uncertainty = ((df_merged.filter(regex=("errors*"))**2).sum(axis=1))**0.5
        # divide by 1/n
        sigma_obs_uncertainty = (1 / df_merged.filter(regex=("errors*")).count(axis=1)) * sigma_obs_uncertainty

        # 2) variability of change between sources
        column_names = df_merged.columns.intersection(df_merged.filter(regex=("changes*")).columns.to_list())
        # calculate standard deviation of all differences from annual mean: TODO: what to do if rate is removed?
        df_diff_from_mean = df_merged[column_names].subtract(mean_changes, axis=0)
        arr_diff_from_mean = df_diff_from_mean[df_diff_from_mean != 0].values.flatten()
        arr_diff_from_mean = arr_diff_from_mean[~pd.isnull(arr_diff_from_mean)]  # remove nans
        stdev_differences = np.std(arr_diff_from_mean) if len(arr_diff_from_mean) > 0 else 0
        # divide stdev_differences by N = number of different observations
        # df_diff_from_mean.count(axis=1) this will give us the number of values that are not NaN per row
        # times 1.96 as we calculate sigma-2 uncertainties (95%)
        sigma_variability_uncertainty = 1.96 * np.array(stdev_differences / df_diff_from_mean.count(axis=1))

        # Combine two uncertainty sources assuming they are independent
        uncertainties = (sigma_obs_uncertainty**2 + sigma_variability_uncertainty**2)**0.5

        df_mean_annual = pd.DataFrame(pd.DataFrame(
            {"start_dates": start_dates, "end_dates": end_dates, "changes": mean_changes, "errors": uncertainties}))

        if add_trend_after_averaging and remove_trend:
            # add mean changes back which have been removed over the common period
            df_mean_annual["changes"] = df_mean_annual["changes"] + np.mean(change_means_over_period)

        # make Timeseries object with combined solution
        ts_data = TimeseriesData(start_dates=np.array(df_mean_annual["start_dates"]),
                                 end_dates=np.array(df_mean_annual["end_dates"]),
                                 changes=np.array(df_mean_annual["changes"]),
                                 errors=np.array(df_mean_annual["errors"]),
                                 glacier_area_reference=None,
                                 glacier_area_observed=None,
                                 hydrological_correction_value=None,
                                 remarks=None)
        reference_dataset_for_metadata = self.datasets[0]  # use this as a reference for filling metadata

        return Timeseries(region=reference_dataset_for_metadata.region, data_group=out_data_group,
                          data=ts_data, unit=reference_dataset_for_metadata.unit, user_group=out_user_group,
                          area_change_applied=reference_dataset_for_metadata.area_change_applied), data_catalogue_out

    def __len__(self) -> int:
        return len(self._datasets)

    def __str__(self):
        return [str(d) for d in self._datasets]
