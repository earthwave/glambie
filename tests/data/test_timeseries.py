import os

from glambie.const.data_groups import GLAMBIE_DATA_GROUPS
from glambie.data.timeseries import Timeseries
from glambie.data.timeseries import TimeseriesData
import numpy as np
import pytest


@pytest.fixture()
def example_timeseries():
    ts = Timeseries(rgi_version=6,
                    unit='m',
                    data_group=GLAMBIE_DATA_GROUPS['altimetry'],
                    data_filepath=os.path.join("tests", "test_data", "datastore", "alaska_altimetry_sharks.csv"))
    return ts


@pytest.fixture()
def example_timeseries_ingested():
    data = TimeseriesData(dates=[2010.1, 2010.2],
                          dates_string=['2010-01-01', '2010-02-01'],
                          changes=np.array([2., 5.]),
                          errors=np.array([1., 1.2]),
                          area_reference=np.array([10000, 10000]),
                          area_observed=np.array([10000, 10000]))
    ts = Timeseries(rgi_version=6,
                    unit='m',
                    data_group=GLAMBIE_DATA_GROUPS['altimetry'],
                    data=data)
    return ts


def test_data_ingestion(example_timeseries_ingested):
    assert example_timeseries_ingested.data.dates is not None
    assert example_timeseries_ingested.is_data_loaded


def test_timeseries_data_class_can_be_instantiated(example_timeseries):
    assert example_timeseries is not None


def test_min_t(example_timeseries_ingested):
    assert example_timeseries_ingested.data.min_time == 2010.1


def test_max_t(example_timeseries_ingested):
    assert example_timeseries_ingested.data.max_time == 2010.2


def test_min_change_value(example_timeseries_ingested):
    assert example_timeseries_ingested.data.min_change_value == 2.


def test_max_change_value(example_timeseries_ingested):
    assert example_timeseries_ingested.data.max_change_value == 5.


def test_temporal_resolution(example_timeseries_ingested):
    assert example_timeseries_ingested.data.temporal_resolution == 0.05


def test_data_as_dataframe(example_timeseries_ingested):
    df = example_timeseries_ingested.data.as_dataframe()
    assert df.shape == (2, 4)


def test_metadata_as_dataframe(example_timeseries):
    df = example_timeseries.metadata_as_dataframe()
    assert df['data_group'].iloc[0] == 'altimetry'
    assert df.shape[0] == 1


def test_timeseries_load_data(example_timeseries):
    example_timeseries.load_data()
    assert example_timeseries.data.dates is not None
    assert example_timeseries.is_data_loaded
