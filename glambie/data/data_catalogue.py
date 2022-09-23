from __future__ import annotations

import json
import os

from glambie.const.data_groups import GLAMBIE_DATA_GROUPS
from glambie.const.regions import REGIONS
from glambie.const.regions import RGIRegion
from glambie.data.timeseries import Timeseries
import pandas as pd


class DataCatalogue():
    """Class containing a catalogue of datasets

    This only contains metadata - all actual data loaded by client
    """

    def __init__(self, base_path: str, datasets: list[Timeseries]):
        self._base_path = base_path
        self._datasets = datasets

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
            data catalogue containing the metadata of datasets, the actual timeseries data will lazy loaded
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
            data catalogue containing the metadata of datasets, the actual timeseries data will lazy loaded
        """
        basepath = os.path.join(*meta_data_dict['basepath'])
        datasets_dict = meta_data_dict['datasets']
        datasets = []
        for ds_dict in datasets_dict:
            fp = os.path.join(basepath, ds_dict['filename'])
            region = REGIONS[ds_dict['region']]
            data_group = GLAMBIE_DATA_GROUPS[ds_dict['data_group']]
            user_group = ds_dict['user_group']
            datasets.append(Timeseries(data_filepath=fp, region=region, data_group=data_group, user_group=user_group))

        return DataCatalogue(basepath, datasets)

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

    def load_all_data(self):
        """
        Loads the timeseries data of all datasets in catalogue
        Only loads data if it is not already loaded in a specific dataset
        """
        for dataset in self.datasets:
            if not dataset.is_data_loaded:
                dataset.load_data()

    def __len__(self) -> int:
        return len(self._datasets)

    def __str__(self):
        return [str(d) for d in self._datasets]
