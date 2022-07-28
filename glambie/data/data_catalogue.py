from __future__ import annotations

from typing import Optional
from webbrowser import get
import pandas as pd
import json

from glambie.const.data_groups import GLAMBIE_DATA_GROUPS
from glambie.const.regions import regions
from glambie.data.timeseries import Timeseries
import os


class DataCatalogue():
    """Class containing a catalogue of datasets

    This only contains metedata - all actual data loaded by client
    """
    def __init__(self, base_path: str, datasets: dict[str, Timeseries]):
        self.base_path = base_path
        self._datasets = datasets

    @staticmethod
    def from_json_file(metadata_file_path: str) -> DataCatalogue:
        with open(metadata_file_path) as json_file:
            DataCatalogue.from_dict(json.load(json_file))

    @staticmethod
    def from_dict(meta_data_dict: dict) -> DataCatalogue:
        basepath = os.path.join(*meta_data_dict['basepath'])
        datasets_dict = meta_data_dict['datasets']
        datasets = []
        for ds_dict in datasets_dict:
            fp = os.path.join(basepath, ds_dict['filename'])
            region = regions[ds_dict['region']]
            data_group = GLAMBIE_DATA_GROUPS[ds_dict['data_group']]
            user_group = ds_dict['user_group']
            dataset = Timeseries(data_filepath=fp, region=region, data_group=data_group, user_group=user_group)
            datasets.append(dataset)

        return DataCatalogue(basepath, datasets)

    @property
    def datasets(self):
        return self._datasets

    @property
    def regions(self):
        return self._regions

    @property
    def basepath(self):
        return self._basepath

    def as_dataframe(self):
        metadata_list = [ds.metadata_as_dataframe() for ds in self._datasets]
        return pd.concat(metadata_list)

    def get_regions(self) -> list:
        return list({s.region for s in self._datasets})  # get as a set, so only unique values

    def get_filtered_datasets(self, region_name: Optional[str] = None, data_group: Optional[str] = None,
                              user_group: Optional[str] = None):
        datasets = self._datasets
        if region_name is not None:  # filter by region
            datasets = [s for s in datasets if s.region.name.lower() == region_name.lower()]
        if data_group is not None:  # filter by data group
            datasets = [s for s in datasets if s.data_group.name.lower() == data_group.lower()]
        if user_group is not None:  # filter by user group
            datasets = [s for s in datasets if s.user_group.lower() == user_group.lower()]
        return self.__class__(self.base_path, datasets)

    def __len__(self) -> int:
        return len(self._datasets)

    def __str__(self):
        return [str(d) for d in self._datasets]
