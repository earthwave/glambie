from glambie.plot.plot_helpers import apply_vertical_adjustment_for_cumulative_plot
from glambie.data.timeseries import TimeseriesData
import numpy as np
import pytest


@pytest.fixture()
def timeseries_data_example1():
    return TimeseriesData(start_dates=[2010, 2011],
                          end_dates=[2011, 2012],
                          changes=np.array([2., 5.]),
                          errors=np.array([1., 1.2]),
                          glacier_area_reference=np.array([10000, 10000]),
                          glacier_area_observed=np.array([10000, 10000]))


@pytest.fixture()
def timeseries_data_example2():
    return TimeseriesData(start_dates=[2012, 2013],
                          end_dates=[2013, 2014],
                          changes=np.array([3., 6.]),
                          errors=np.array([1., 1.2]),
                          glacier_area_reference=np.array([10000, 10000]),
                          glacier_area_observed=np.array([10000, 10000]))


def test_apply_vertical_adjustment_for_cumulative_plot(timeseries_data_example1, timeseries_data_example2):
    reference_timeseries = timeseries_data_example1.as_cumulative_timeseries()
    timeseries_to_adjust = timeseries_data_example2.as_cumulative_timeseries()
    adjusted_series = apply_vertical_adjustment_for_cumulative_plot(timeseries_to_adjust=timeseries_to_adjust,
                                                                    reference_timeseries=reference_timeseries)
    assert all(a == b for a, b in zip(timeseries_to_adjust.dates, adjusted_series.dates))
    assert all(a == b for a, b in zip(timeseries_to_adjust.changes + 7.0, adjusted_series.changes))


def test_apply_vertical_adjustment_for_cumulative_plot_not_on_monthly_grid(timeseries_data_example1,
                                                                           timeseries_data_example2):
    reference_timeseries = timeseries_data_example1.as_cumulative_timeseries()
    timeseries_to_adjust = timeseries_data_example2.as_cumulative_timeseries()
    adjusted_series = apply_vertical_adjustment_for_cumulative_plot(timeseries_to_adjust=timeseries_to_adjust,
                                                                    reference_timeseries=reference_timeseries)
    timeseries_to_adjust.dates = timeseries_to_adjust.dates + 0.01
    adjusted_series_off_grid = apply_vertical_adjustment_for_cumulative_plot(timeseries_to_adjust=timeseries_to_adjust,
                                                                             reference_timeseries=reference_timeseries)
    assert all(a == b for a, b in zip(adjusted_series.changes, adjusted_series_off_grid.changes))


def test_apply_vertical_adjustment_for_cumulative_plot_with_interpolation(timeseries_data_example1,
                                                                          timeseries_data_example2):
    reference_timeseries = timeseries_data_example1.as_cumulative_timeseries()
    timeseries_to_adjust = timeseries_data_example2.as_cumulative_timeseries()
    timeseries_to_adjust.dates = timeseries_to_adjust.dates - 11. / 12.

    adjusted_series = apply_vertical_adjustment_for_cumulative_plot(timeseries_to_adjust=timeseries_to_adjust,
                                                                    reference_timeseries=reference_timeseries)
    expected_changes = timeseries_to_adjust.changes + (2.0 + 5.0 / 12.0)
    assert all(pytest.approx(a, b) for a, b in zip(expected_changes, adjusted_series.changes))


def test_apply_vertical_adjustment_for_cumulative_plot_outside_reference_dataset(timeseries_data_example1,
                                                                                 timeseries_data_example2):
    reference_timeseries = timeseries_data_example1.as_cumulative_timeseries()
    timeseries_to_adjust = timeseries_data_example2.as_cumulative_timeseries()
    timeseries_to_adjust.dates = timeseries_to_adjust.dates - 3.0  # shift so it starts earlier than reference series

    adjusted_series = apply_vertical_adjustment_for_cumulative_plot(timeseries_to_adjust=timeseries_to_adjust,
                                                                    reference_timeseries=reference_timeseries)
    expected_changes = timeseries_to_adjust.changes + (-3.0)
    assert all(pytest.approx(a, b) for a, b in zip(expected_changes, adjusted_series.changes))
