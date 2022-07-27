from typing import Optional
import pandas as pd
import json
from glambie.const.data_groups import GlambieDataGroups
from glambie.const.regions import Regions
from glambie.data.timeseries_data import ChangeTimeseries
import os


class DataCatalogue():
    """Class containing a catalogue of datasets
    """

    @property
    def datasets(self):
        return self._datasets

    @property
    def regions(self):
        return self._regions

    @property
    def basepath(self):
        return self._basepath

    def __init__(self, meta_data: dict, read_data: bool = False):
        self._basepath = os.path.join(*meta_data['basepath'])
        datasets_dict = meta_data['datasets']
        self._datasets = []
        for ds_dict in datasets_dict:
            fp = os.path.join(self._basepath, ds_dict['filename'])
            region = Regions.get_region_by_name(ds_dict['region'])
            data_group = GlambieDataGroups.get_data_group_by_name(ds_dict['data_group'])
            user_group = ds_dict['user_group']
            dataset = ChangeTimeseries(data_filepath=fp, region=region, data_group=data_group, user_group=user_group,
                                       read_data=read_data)
            self._datasets.append(dataset)

    @staticmethod
    def from_file(metadata_file_path: str):
        with open(metadata_file_path) as json_file:
            meta_data = json.load(json_file)
            print(type(meta_data))
            return DataCatalogue(meta_data)

    def as_dataframe(self):
        metadata_list = [ds.metadata_as_dataframe() for ds in self.datasets]
        return pd.concat(metadata_list)

    def __len__(self) -> int:
        return len(self.datasets)

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
        return datasets

    def __str__(self):
        return [str(d) for d in self.datasets]
