import numpy as np
import pytest
from glambie.data.timeseries_data import ChangeTimeseries
from glambie.const.data_groups import GlambieDataGroups


@pytest.fixture()
def example_timeseries():
    ts = ChangeTimeseries(rgi_version=6,
                          unit='m',
                          data_group=GlambieDataGroups.get('altimetry'))
    return ts


@pytest.fixture()
def example_timeseries_ingested():
    ts = ChangeTimeseries(rgi_version=6,
                          unit='m',
                          data_group=GlambieDataGroups.get('altimetry'))
    ts.ingest_data(dates=[2010.1, 2010.2],
                   changes=np.array([2., 5.]),
                   errors=np.array([1., 1.2]),
                   area=np.array([10000, 10000]))
    return ts


def test_data_ingestion(example_timeseries):
    example_timeseries.ingest_data(dates=[2010.1, 2010.2],
                                   changes=np.array([2., 5.]),
                                   errors=np.array([1., 1.2]),
                                   area=np.array([10000, 10000]))
    assert example_timeseries.dates is not None


def test_timeseries_data_class_can_be_instantiated(example_timeseries):
    assert example_timeseries is not None


def test_min_t(example_timeseries_ingested):
    assert example_timeseries_ingested.min_time == 2010.1


def test_max_t(example_timeseries_ingested):
    assert example_timeseries_ingested.max_time == 2010.2


def test_min_change_value(example_timeseries_ingested):
    assert example_timeseries_ingested.min_change_value == 2.


def test_max_change_value(example_timeseries_ingested):
    assert example_timeseries_ingested.max_change_value == 5.


def test_temporal_resolution(example_timeseries_ingested):
    assert example_timeseries_ingested.temporal_resolution() == 0.05


def test_data_as_dataframe(example_timeseries_ingested):
    df = example_timeseries_ingested.data_as_dataframe()
    assert df.shape == (2, 4)


def test_metadata_as_dataframe(example_timeseries):
    df = example_timeseries.metadata_as_dataframe()
    assert df['data_group'].iloc[0] == 'altimetry'
    assert df.shape[0] == 1
