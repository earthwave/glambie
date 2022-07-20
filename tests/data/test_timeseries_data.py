import numpy as np
import pytest
from glambie.data.timeseries_data import ChangeTimeseries


@pytest.fixture()
def example_timeseries():
    return ChangeTimeseries(dates=[2010.1, 2010.2],
                            change=np.array([2., 5.]),
                            errors=np.array([1., 1.2]),
                            area=np.array([10000, 10000]),
                            rgi_version=6,
                            region_id=7,
                            unit='m'
                            )


def test_timeseries_data_class_can_be_instantiated(example_timeseries):
    assert example_timeseries is not None


def test_min_t(example_timeseries):
    assert example_timeseries.min_time == 2010.1


def test_max_t(example_timeseries):
    assert example_timeseries.max_time == 2010.2


def test_min_change_value(example_timeseries):
    assert example_timeseries.min_change_value == 2.


def test_max_change_value(example_timeseries):
    assert example_timeseries.max_change_value == 5.


def test_temporal_resolution(example_timeseries):
    assert example_timeseries.temporal_resolution() == 0.05
