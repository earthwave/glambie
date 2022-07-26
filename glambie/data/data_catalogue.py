
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

    def __init__(self, meta_data: dict):
        self._basepath = os.path.join(*meta_data['basepath'])
        datasets_dict = meta_data['datasets']
        self._datasets = []
        for ds_dict in datasets_dict:
            fp = os.path.join(self._basepath, ds_dict['filename'])
            region = Regions.get_region_by_name(ds_dict['region'])
            data_group = GlambieDataGroups.get_data_group_by_name(ds_dict['data_group'])
            user_group = ds_dict['user_group']
            dataset = ChangeTimeseries(data_filepath=fp, region=region, data_group=data_group, user_group=user_group)
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

    def get_datasets_by_region(self, region_name: str):
        return [s for s in self._datasets if s.region.name.lower() == region_name.lower()]

    def __str__(self):
        return [str(d) for d in self.datasets]
