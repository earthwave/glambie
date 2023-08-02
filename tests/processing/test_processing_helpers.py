from glambie.processing.processing_helpers import filter_catalogue_with_config_settings
from glambie.processing.processing_helpers import slice_timeseries_at_gaps
from glambie.processing.processing_helpers import check_and_handle_gaps_in_timeseries
from glambie.const.data_groups import GLAMBIE_DATA_GROUPS
from glambie.data.data_catalogue import DataCatalogue
from glambie.data.timeseries import TimeseriesData, Timeseries
from glambie.config.config_classes import GlambieRunConfig
from glambie.const.regions import REGIONS
import pytest
import os
import pandas as pd
import numpy as np


@pytest.fixture()
def example_catalogue_1():
    return DataCatalogue.from_dict({"base_path": ["tests", "test_data", "datastore"],
                                    "datasets": [
        {
            "filename": "xx.csv",
            "region": "svalbard",
            "user_group": "sharks",
            "data_group": "altimetry",
            "unit": "m"
        },
        {
            "filename": "xx.csv",
            "region": "svalbard",
            "user_group": "lions",
            "data_group": "altimetry",
            "unit": "m"
        }]})


@pytest.fixture()
def example_catalogue_2():
    return DataCatalogue.from_dict({"base_path": ["tests", "test_data", "datastore"],
                                    "datasets": [
        {
            "filename": "xx.csv",
            "region": "svalbard",
            "user_group": "sharks",
            "data_group": "demdiff",
            "unit": "m"
        },
        {
            "filename": "xx.csv",
            "region": "svalbard",
            "user_group": "sloths",
            "data_group": "demdiff",
            "unit": "m"
        },
        {
            "filename": "xx.csv",
            "region": "svalbard",
            "user_group": "lions",
            "data_group": "glaciological",
            "unit": "mwe"
        },
        {
            "filename": "xx.csv",
            "region": "svalbard",
            "user_group": "dolphins",
            "data_group": "glaciological",
            "unit": "mwe"
        }]})


@pytest.fixture()
def example_catalogue_filled():
    data1 = TimeseriesData(start_dates=[2010, 2011, 2012],
                           end_dates=[2011, 2012, 2018],
                           changes=np.array([2., 5., 7.]),
                           errors=np.array([1., 1.2, 1.3]),
                           glacier_area_reference=np.array([None, None]),
                           glacier_area_observed=np.array([None, None]),
                           hydrological_correction_value=None,
                           remarks=None)
    ts1 = Timeseries(rgi_version=6,
                     unit='mwe',
                     user_group="a",
                     data_group=GLAMBIE_DATA_GROUPS['consensus'],
                     data=data1,
                     region=REGIONS["iceland"])
    data2 = TimeseriesData(start_dates=[2010, 2011],
                           end_dates=[2011, 2012],
                           changes=np.array([3., 4.]),
                           errors=np.array([0.9, 1.1]),
                           glacier_area_reference=np.array([None, None]),
                           glacier_area_observed=np.array([None, None]),
                           hydrological_correction_value=None,
                           remarks=None)
    ts2 = Timeseries(rgi_version=6,
                     unit='mwe',
                     user_group="b",
                     data_group=GLAMBIE_DATA_GROUPS['consensus'],
                     data=data2,
                     region=REGIONS["svalbard"])
    return DataCatalogue.from_list([ts1, ts2])


@pytest.fixture()
def glambie_config():
    yaml_abspath = os.path.join('tests', 'test_data', 'configs', 'test_config.yaml')
    return GlambieRunConfig.from_yaml(yaml_abspath)


def test_filter_catalogue_with_config_settings(example_catalogue_1, glambie_config):
    data_group = GLAMBIE_DATA_GROUPS["altimetry"]
    data_catalogue = example_catalogue_1
    region_config = glambie_config.regions[1]

    datasets_annual, datasets_trend = filter_catalogue_with_config_settings(data_group=data_group,
                                                                            region_config=region_config,
                                                                            data_catalogue=data_catalogue)
    # we should have filtered out lions from this dataset
    assert len(datasets_annual.datasets) == 1
    assert all(d.user_group != "lions" for d in datasets_annual.datasets)

    # we should have filtered out sharks from this dataset
    assert len(datasets_annual.datasets) == 1
    assert all(d.user_group != "sharks" for d in datasets_trend.datasets)


def test_filter_catalogue_with_config_settings_demdiff_and_glaciological(example_catalogue_2, glambie_config):
    data_group = GLAMBIE_DATA_GROUPS["demdiff_and_glaciological"]
    data_catalogue = example_catalogue_2
    region_config = glambie_config.regions[1]

    datasets_annual, datasets_trend = filter_catalogue_with_config_settings(data_group=data_group,
                                                                            region_config=region_config,
                                                                            data_catalogue=data_catalogue)
    # we should have filtered out lions from this dataset
    assert len(datasets_annual.datasets) == 1
    assert all(d.user_group != "lions" for d in datasets_annual.datasets)
    assert all(d.data_group != GLAMBIE_DATA_GROUPS["demdiff"] for d in datasets_annual.datasets)
    assert any(d.user_group == "dolphins" for d in datasets_annual.datasets)

    # we should have filtered out sharks from this dataset
    assert len(datasets_annual.datasets) == 1
    assert all(d.user_group != "sharks" for d in datasets_trend.datasets)
    assert all(d.data_group != GLAMBIE_DATA_GROUPS["glaciological"] for d in datasets_trend.datasets)
    assert any(d.user_group == "sloths" for d in datasets_trend.datasets)


def test_slice_timeseries_at_gaps():
    ts = pd.DataFrame({"start_dates": [2012, 2013, 2015, 2016, 2020],
                       "end_dates": [2013, 2014, 2016, 2017, 2023],
                       "changes": [2, 3, 4, 5, 6]})
    split_ts_result = slice_timeseries_at_gaps(ts)
    expected_split_ts_result = [
        pd.DataFrame({"start_dates": [2012, 2013],
                      "end_dates": [2013, 2014],
                      "changes": [2, 3]}),
        pd.DataFrame({"start_dates": [2015, 2016],
                      "end_dates": [2016, 2017],
                      "changes": [4, 5]}),
        pd.DataFrame({"start_dates": [2020],
                      "end_dates": [2023],
                      "changes": [6]})]

    for (calculated, expected) in zip(split_ts_result, expected_split_ts_result):
        pd.testing.assert_frame_equal(calculated, expected)


def test_check_and_handle_gaps_in_timeseries(example_catalogue_filled):
    example_catalogue_filled.copy()
    # introduce a gap
    example_catalogue_filled.datasets[
        1].data.start_dates[1] = example_catalogue_filled.datasets[1].data.start_dates[1] + 0.5
    assert not example_catalogue_filled.datasets[1].data.is_cumulative_valid()
    result_catalogue, split_dataset_names = check_and_handle_gaps_in_timeseries(example_catalogue_filled)
    # now we should have one more dataset as it has been split up due to the gap
    assert len(result_catalogue.datasets) == len(example_catalogue_filled.datasets) + 1
    # and no more gaps in the data
    for dataset in result_catalogue.datasets:
        assert dataset.data.is_cumulative_valid()
    assert np.array_equal(split_dataset_names, [[example_catalogue_filled.datasets[1].user_group + "_1",
                                                 example_catalogue_filled.datasets[1].user_group + "_2"]])
