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
                    data_group=GLAMBIE_DATA_GROUPS['demdiff'],
                    data_filepath=os.path.join("tests", "test_data", "datastore", "central_asia_demdiff_sharks.csv"))
    return ts


@pytest.fixture()
def example_timeseries_ingested():
    data = TimeseriesData(start_dates=[2010.1, 2010.2],
                          end_dates=[2010.2, 2010.3],
                          changes=np.array([2., 5.]),
                          errors=np.array([1., 1.2]),
                          glacier_area_reference=np.array([10000, 10000]),
                          glacier_area_observed=np.array([10000, 10000]))
    ts = Timeseries(rgi_version=6,
                    unit='m',
                    data_group=GLAMBIE_DATA_GROUPS['demdiff'],
                    data=data)
    return ts


def test_data_ingestion(example_timeseries_ingested):
    assert example_timeseries_ingested.data.start_dates is not None
    assert example_timeseries_ingested.is_data_loaded


def test_timeseries_data_class_can_be_instantiated(example_timeseries):
    assert example_timeseries is not None


def test_min_t_startdate(example_timeseries_ingested):
    assert example_timeseries_ingested.data.min_start_date == 2010.1


def test_min_t_enddate(example_timeseries_ingested):
    assert example_timeseries_ingested.data.min_end_date == 2010.2


def test_max_t_startdate(example_timeseries_ingested):
    assert example_timeseries_ingested.data.max_start_date == 2010.2


def test_max_t_enddate(example_timeseries_ingested):
    assert example_timeseries_ingested.data.max_end_date == 2010.3


def test_min_change_value(example_timeseries_ingested):
    assert example_timeseries_ingested.data.min_change_value == 2.


def test_max_change_value(example_timeseries_ingested):
    assert example_timeseries_ingested.data.max_change_value == 5.


def test_min_temporal_resolution(example_timeseries_ingested):
    assert example_timeseries_ingested.data.min_temporal_resolution == 0.1


def test_max_temporal_resolution(example_timeseries_ingested):
    assert example_timeseries_ingested.data.max_temporal_resolution == 0.1


def test_data_as_dataframe(example_timeseries_ingested):
    df = example_timeseries_ingested.data.as_dataframe()
    assert df.shape == (2, 6)


def test_metadata_as_dataframe(example_timeseries):
    df = example_timeseries.metadata_as_dataframe()
    assert df['data_group'].iloc[0] == 'demdiff'
    assert df.shape[0] == 1


def test_timeseries_load_data(example_timeseries):
    example_timeseries.load_data()
    assert example_timeseries.data.start_dates is not None
    assert example_timeseries.is_data_loaded
