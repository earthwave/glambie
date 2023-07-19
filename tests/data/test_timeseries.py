import warnings
import pandas as pd
import pytest
import numpy as np
import os

from glambie.const.data_groups import GLAMBIE_DATA_GROUPS
from glambie.const.regions import REGIONS
from glambie.data.timeseries import Timeseries
from glambie.data.timeseries import TimeseriesData
from glambie.const import constants
from glambie.const.density_uncertainty import get_density_uncertainty_over_survey_period
from glambie.util.mass_height_conversions import meters_to_meters_water_equivalent
from glambie.util.mass_height_conversions import meters_water_equivalent_to_gigatonnes


@pytest.fixture()
def example_timeseries():
    ts = Timeseries(rgi_version=6,
                    unit='m',
                    data_group=GLAMBIE_DATA_GROUPS['demdiff'],
                    data_filepath=os.path.join("tests", "test_data", "datastore", "central_asia_demdiff_sharks.csv"),
                    additional_metadata={'toves': 'slithy', 'mome raths': 'outgrabe'})
    return ts


@pytest.fixture()
def example_timeseries_ingested():
    data = TimeseriesData(start_dates=[2010.1, 2010.2],
                          end_dates=[2010.2, 2010.3],
                          changes=np.array([2., 5.]),
                          errors=np.array([1., 1.2]),
                          glacier_area_reference=np.array([10000, 10000]),
                          glacier_area_observed=np.array([10000, 10000]),
                          hydrological_correction_value=None,
                          remarks=np.array(['thunder', 'lightning']))
    ts = Timeseries(rgi_version=6,
                    unit='m',
                    data_group=GLAMBIE_DATA_GROUPS['demdiff'],
                    data=data,
                    region=REGIONS["iceland"])
    return ts


def test_save_as_csv(tmp_path, example_timeseries_ingested):
    out_csv_path = os.path.join(tmp_path, "out_csv_test.csv")
    example_timeseries_ingested.save_data_as_csv(out_csv_path)
    assert os.path.exists(out_csv_path)
    df = pd.read_csv(out_csv_path)
    # check data read from CSV is same as TimeseriesData
    pd.testing.assert_frame_equal(df, example_timeseries_ingested.data.as_dataframe(), check_dtype=False)


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
    assert df.shape == (2, 8)


def test_metadata_as_dataframe(example_timeseries):
    df = example_timeseries.metadata_as_dataframe()
    assert df['data_group'].iloc[0] == 'demdiff'
    assert df.shape[0] == 1


def test_timeseries_load_data(example_timeseries):
    example_timeseries.load_data()
    assert example_timeseries.data.start_dates is not None
    assert example_timeseries.is_data_loaded


def test_is_cumulative_valid(example_timeseries_ingested):
    # example timeseries is valid
    assert example_timeseries_ingested.data.is_cumulative_valid()

    # case 1: gaps in timeseries, should result in False
    example_timeseries_ingested.data.start_dates = [2010.1, 2010.2]
    example_timeseries_ingested.data.end_dates = [2010.17, 2010.3]
    assert not example_timeseries_ingested.data.is_cumulative_valid()

    # case 2: overlapping timeseries, should result in False
    example_timeseries_ingested.data.start_dates = [2010.1, 2010.2]
    example_timeseries_ingested.data.end_dates = [2010.3, 2010.5]
    assert not example_timeseries_ingested.data.is_cumulative_valid()


def test_as_cumulative_timeseries(example_timeseries_ingested):
    df_cumulative = example_timeseries_ingested.data.as_cumulative_timeseries()
    pd.testing.assert_series_equal(df_cumulative["dates"], pd.Series([2010.1, 2010.2, 2010.3], name="dates"))
    pd.testing.assert_series_equal(df_cumulative["changes"], pd.Series([0, 2.0, 7.0], name="changes"))


def test_as_cumulative_timeseries_raises_warning(example_timeseries_ingested):
    with warnings.catch_warnings(record=True) as w:
        # Cause all warnings to always be triggered
        warnings.simplefilter("always")
        # Trigger a warning
        example_timeseries_ingested.data.end_dates = [2010.17, 2010.3]  # change end dates so ther is a data gap
        example_timeseries_ingested.data.as_cumulative_timeseries()  # this should trigger warning
        # Verify warning has been triggered
        assert len(w) == 1
        assert "invalid" in str(w[-1].message)


def test_convert_timeseries_to_unit_mwe_from_m(example_timeseries_ingested):
    density_of_water = 997
    density_of_ice = 850
    converted_timeseries = example_timeseries_ingested.convert_timeseries_to_unit_mwe(
        density_of_water=density_of_water, density_of_ice=density_of_ice)
    assert converted_timeseries.unit == "mwe"
    assert example_timeseries_ingested.unit == "m"
    assert not np.array_equal(converted_timeseries.data.changes, example_timeseries_ingested.data.changes)
    expected_converted_changes = example_timeseries_ingested.data.changes / density_of_water * density_of_ice
    assert np.array_equal(converted_timeseries.data.changes, expected_converted_changes)


def test_convert_timeseries_to_unit_mwe_from_gt(example_timeseries_ingested):
    density_of_water = 997
    example_timeseries_ingested.unit = "gt"
    converted_timeseries = example_timeseries_ingested.convert_timeseries_to_unit_mwe(
        density_of_water=density_of_water, rgi_area_version=6)
    assert example_timeseries_ingested.unit == "gt"
    assert not np.array_equal(converted_timeseries.data.changes, example_timeseries_ingested.data.changes)
    assert not np.array_equal(converted_timeseries.data.errors, example_timeseries_ingested.data.errors)
    expected_converted_changes = (1e6 * example_timeseries_ingested.data.changes) / (
        example_timeseries_ingested.region.rgi6_area * density_of_water)
    assert np.array_equal(converted_timeseries.data.changes, expected_converted_changes)


def test_convert_timeseries_to_unit_mwe_from_gt_and_back(example_timeseries_ingested):
    density_of_water = 997
    example_timeseries_ingested.unit = "gt"
    converted_timeseries_mwe = example_timeseries_ingested.convert_timeseries_to_unit_mwe(
        density_of_water=density_of_water, rgi_area_version=6)
    converted_timeseries_gt = converted_timeseries_mwe.convert_timeseries_to_unit_gt(
        density_of_water=density_of_water, rgi_area_version=6)
    assert not np.array_equal(converted_timeseries_mwe.data.changes, example_timeseries_ingested.data.changes)
    # allclose due to floating points
    assert np.allclose(converted_timeseries_gt.data.changes, example_timeseries_ingested.data.changes)
    assert np.allclose(converted_timeseries_gt.data.errors, example_timeseries_ingested.data.errors)


def test_convert_timeseries_to_unit_mwe_no_conversion_when_already_in_mwe(example_timeseries_ingested):
    example_timeseries_ingested.unit = "mwe"
    converted_timeseries = example_timeseries_ingested.convert_timeseries_to_unit_mwe()
    assert np.array_equal(converted_timeseries.data.changes, example_timeseries_ingested.data.changes)


def test_convert_timeseries_to_unit_test_uncertainties(example_timeseries_ingested):
    density_of_water = 997
    density_of_ice = 850
    converted_timeseries = example_timeseries_ingested.convert_timeseries_to_unit_mwe(
        density_of_water=density_of_water, density_of_ice=density_of_ice)
    assert not np.array_equal(converted_timeseries.data.errors, example_timeseries_ingested.data.errors)
    #
    df = example_timeseries_ingested.data.as_dataframe()
    changes_mwe = np.array(meters_to_meters_water_equivalent(df.changes, density_of_water=density_of_water,
                                                             density_of_ice=density_of_ice))
    errors_mw = np.array(meters_to_meters_water_equivalent(df.errors, density_of_water=density_of_water,
                                                           density_of_ice=density_of_ice))
    density_unc = get_density_uncertainty_over_survey_period(0.1)  # over one month
    expected_errors_mwe_with_density_error = np.abs(changes_mwe) * ((errors_mw / changes_mwe)**2
                                                                    + (density_unc / density_of_ice)**2)**0.5
    assert np.array_equal(converted_timeseries.data.errors, expected_errors_mwe_with_density_error)


def test_convert_timeseries_to_unit_gt_no_area_change_rate(example_timeseries_ingested):
    example_timeseries_ingested.unit = "mwe"
    example_timeseries_ingested.region = REGIONS["iceland"]
    converted_timeseries = example_timeseries_ingested.convert_timeseries_to_unit_gt()
    assert str.lower(converted_timeseries.unit) == "gt"
    assert example_timeseries_ingested.unit == "mwe"
    assert not np.array_equal(converted_timeseries.data.changes, example_timeseries_ingested.data.changes)
    area = example_timeseries_ingested.region.rgi6_area
    expected_converted_changes = example_timeseries_ingested.data.changes * 997 * (area / 1e6)
    assert np.array_equal(converted_timeseries.data.changes, expected_converted_changes)


def test_timeseries_is_monthly_grid(example_timeseries_ingested):
    assert not example_timeseries_ingested.timeseries_is_monthly_grid()
    example_timeseries_ingested.data.start_dates = [2010, 2010 + 1 / 12]
    example_timeseries_ingested.data.end_dates = [2010 + 1 / 12, 2010 + 2 / 12]
    assert example_timeseries_ingested.timeseries_is_monthly_grid()


def test_convert_timeseries_to_monthly_grid(example_timeseries_ingested):
    # 1) the case where we are resampling since it is monthly resolution
    example_timeseries_converted = example_timeseries_ingested.convert_timeseries_to_monthly_grid()
    assert example_timeseries_converted.timeseries_is_monthly_grid()
    assert not np.array_equal(example_timeseries_ingested.data.changes, example_timeseries_converted.data.changes)
    assert example_timeseries_ingested.data.changes.sum() == example_timeseries_converted.data.changes.sum()
    # 2) the case where we are shifting since it is less high
    example_timeseries_ingested.data.start_dates = [2010.1, 2011.1]
    example_timeseries_ingested.data.end_dates = [2011.1, 2012.1]
    example_timeseries_converted2 = example_timeseries_ingested.convert_timeseries_to_monthly_grid()
    assert not np.array_equal(example_timeseries_ingested.data.start_dates,
                              example_timeseries_converted2.data.start_dates)
    assert not np.array_equal(example_timeseries_ingested.data.end_dates,
                              example_timeseries_converted2.data.end_dates)
    # changes should still be the same as it was shifted
    assert np.array_equal(example_timeseries_ingested.data.changes, example_timeseries_converted2.data.changes)
    assert np.array_equal(example_timeseries_converted2.data.start_dates, np.array([2010 + 1 / 12, 2011 + 1 / 12]))
    assert np.array_equal(example_timeseries_converted2.data.end_dates, np.array([2011 + 1 / 12, 2012 + 1 / 12]))


def test_convert_timeseries_to_annual_trends_down_sampling(example_timeseries_ingested):
    # we are resampling since it is monthly resolution
    example_timeseries_ingested.data.start_dates = np.linspace(2010, 2011, 13)[:-1]
    example_timeseries_ingested.data.end_dates = np.linspace(2010, 2011, 13)[1:]
    example_timeseries_ingested.data.changes = np.linspace(1, 11, 12)
    example_timeseries_ingested.data.errors = np.linspace(1, 2, 12)
    assert not example_timeseries_ingested.timeseries_is_annual_grid()
    example_timeseries_converted = example_timeseries_ingested.convert_timeseries_to_annual_trends()
    assert example_timeseries_converted.timeseries_is_annual_grid()
    assert len(example_timeseries_converted.data.changes) == 1
    assert example_timeseries_converted.data.changes[0] == example_timeseries_ingested.data.changes.sum()

    # add one more month and check it's still the same
    np.append(example_timeseries_ingested.data.start_dates, 2011)
    np.append(example_timeseries_ingested.data.end_dates, 2011 + 1 / 12)
    np.append(example_timeseries_ingested.data.changes, 5)
    np.append(example_timeseries_ingested.data.errors, 2.1)
    example_timeseries_converted2 = example_timeseries_ingested.convert_timeseries_to_annual_trends()
    # should be the same now, and last element is ignored as its not a full year
    assert np.array_equal(example_timeseries_converted.data.changes, example_timeseries_converted2.data.changes)
    assert np.array_equal(example_timeseries_converted.data.errors, example_timeseries_converted2.data.errors)
    assert np.array_equal(example_timeseries_converted.data.start_dates, example_timeseries_converted2.data.start_dates)

    # now we pop 2 elements and should get back no result as not a full year anymore
    example_timeseries_ingested.data.start_dates = example_timeseries_ingested.data.start_dates[:-2]
    example_timeseries_ingested.data.end_dates = example_timeseries_ingested.data.end_dates[:-2]
    example_timeseries_ingested.data.changes = example_timeseries_ingested.data.changes[:-2]
    example_timeseries_ingested.data.errors = example_timeseries_ingested.data.errors[:-2]
    example_timeseries_converted2 = example_timeseries_ingested.convert_timeseries_to_annual_trends()
    assert example_timeseries_converted2.timeseries_is_annual_grid()
    assert len(example_timeseries_converted2.data.changes) == 0
    assert len(example_timeseries_converted2.data.errors) == 0


def test_convert_timeseries_to_annual_trends_down_sampling_errors(example_timeseries_ingested):
    # we are resampling since it is monthly resolution
    example_timeseries_ingested.data.start_dates = np.linspace(2010, 2011, 13)[:-1]
    example_timeseries_ingested.data.end_dates = np.linspace(2010, 2011, 13)[1:]
    example_timeseries_ingested.data.changes = np.linspace(1, 11, 12)
    example_timeseries_ingested.data.errors = np.linspace(1, 2, 12)
    example_timeseries_converted = example_timeseries_ingested.convert_timeseries_to_annual_trends()
    assert len(example_timeseries_converted.data.errors) == 1
    assert example_timeseries_converted.data.errors[0] == np.sqrt(np.nansum(example_timeseries_ingested.
                                                                            data.errors**2)) / len(
                                                                                example_timeseries_ingested.data.errors)


def test_convert_timeseries_to_annual_trends_down_sampling_glaciological_year(example_timeseries_ingested):
    # we are resampling since it is monthly resolution
    example_timeseries_ingested.region = REGIONS["iceland"]
    example_timeseries_ingested.region.glaciological_year_start = 0.75
    example_timeseries_ingested.data.start_dates = np.linspace(2010.75, 2011.75, 13)[:-1]
    example_timeseries_ingested.data.end_dates = np.linspace(2010.75, 2011.75, 13)[1:]
    example_timeseries_ingested.data.changes = np.linspace(1, 11, 12)
    example_timeseries_ingested.data.errors = np.linspace(1, 2, 12)
    assert not example_timeseries_ingested.timeseries_is_annual_grid(year_type=constants.YearType.GLACIOLOGICAL)
    example_timeseries_converted = example_timeseries_ingested.convert_timeseries_to_annual_trends(
        year_type=constants.YearType.GLACIOLOGICAL)
    assert example_timeseries_converted.timeseries_is_annual_grid(year_type=constants.YearType.GLACIOLOGICAL)
    assert len(example_timeseries_converted.data.changes) == 1
    assert example_timeseries_converted.data.changes[0] == example_timeseries_ingested.data.changes.sum()


def test_convert_timeseries_to_annual_trends_up_sampling(example_timeseries_ingested):
    # we are resampling since it is monthly resolution
    example_timeseries_ingested.data.start_dates = np.array([2010.0])
    example_timeseries_ingested.data.end_dates = np.array([2015.0])
    example_timeseries_ingested.data.changes = np.array([5.0])
    example_timeseries_ingested.data.errors = np.array([1.0])
    example_timeseries_ingested.data.glacier_area_reference = None
    example_timeseries_ingested.data.glacier_area_observed = None
    example_timeseries_ingested.data.remarks = np.array(['wibble'])

    example_timeseries_converted = example_timeseries_ingested.convert_timeseries_to_annual_trends()
    assert example_timeseries_converted.timeseries_is_annual_grid()
    assert len(example_timeseries_converted.data.changes) == 5
    assert np.array_equal(example_timeseries_converted.data.start_dates, np.linspace(2010, 2014, 5))
    assert np.array_equal(example_timeseries_converted.data.end_dates, np.linspace(2011, 2015, 5))
    assert example_timeseries_converted.data.changes.sum() == example_timeseries_ingested.data.changes.sum()
    assert np.array_equal(example_timeseries_converted.data.changes, np.linspace(1, 1, 5))
    assert np.array_equal(example_timeseries_converted.data.errors, np.linspace(0.2, 0.2, 5))


def test_convert_timeseries_to_annual_trends_up_sampling_throws_exception(example_timeseries_ingested):
    # we are resampling since it is monthly resolution
    example_timeseries_ingested.data.start_dates = np.array([2010.1])  # not in annual grid
    example_timeseries_ingested.data.end_dates = np.array([2015.0])
    example_timeseries_ingested.data.changes = np.array([5.0])
    assert not example_timeseries_ingested.timeseries_is_annual_grid()
    with pytest.raises(AssertionError):
        example_timeseries_ingested.convert_timeseries_to_annual_trends()


def test_convert_timeseries_to_annual_trends_up_annual_should_return_same_as_input(example_timeseries_ingested):
    example_timeseries_ingested.region = REGIONS["iceland"]
    example_timeseries_ingested.region.glaciological_year_start = 0.75
    example_timeseries_ingested.data.start_dates = np.linspace(2010.75, 2015.75, 6)
    example_timeseries_ingested.data.end_dates = np.linspace(2011.75, 2016.75, 6)
    example_timeseries_ingested.data.changes = np.linspace(1, 6, 6)
    example_timeseries_ingested.data.errors = np.linspace(1, 2, 6)
    assert example_timeseries_ingested.timeseries_is_annual_grid(year_type=constants.YearType.GLACIOLOGICAL)
    example_timeseries_converted = example_timeseries_ingested \
        .convert_timeseries_to_annual_trends(year_type=constants.YearType.GLACIOLOGICAL)
    assert example_timeseries_converted.timeseries_is_annual_grid(year_type=constants.YearType.GLACIOLOGICAL)
    assert np.array_equal(example_timeseries_converted.data.start_dates, example_timeseries_ingested.data.start_dates)
    assert np.array_equal(example_timeseries_converted.data.end_dates, example_timeseries_ingested.data.end_dates)
    assert np.array_equal(example_timeseries_converted.data.changes, example_timeseries_ingested.data.changes)


def test_timeseries_is_annual_grid(example_timeseries_ingested):
    assert not example_timeseries_ingested.timeseries_is_annual_grid(year_type=constants.YearType.CALENDAR)
    example_timeseries_ingested.data.start_dates = [2010, 2011]
    example_timeseries_ingested.data.end_dates = [2011, 2012]
    assert example_timeseries_ingested.timeseries_is_annual_grid(year_type=constants.YearType.CALENDAR)
    example_timeseries_ingested.data.end_dates = [2011, 2012.1]
    assert not example_timeseries_ingested.timeseries_is_annual_grid(year_type=constants.YearType.CALENDAR)


def test_timeseries_is_annual_grid_glaciological_year(example_timeseries_ingested):
    example_timeseries_ingested.region = REGIONS["iceland"]
    example_timeseries_ingested.region.glaciological_year_start = 0.75
    assert not example_timeseries_ingested.timeseries_is_annual_grid(year_type=constants.YearType.GLACIOLOGICAL)
    example_timeseries_ingested.data.start_dates = [2010.75, 2011.75]
    example_timeseries_ingested.data.end_dates = [2011.75, 2012.75]
    assert example_timeseries_ingested.timeseries_is_annual_grid(year_type=constants.YearType.GLACIOLOGICAL)
    example_timeseries_ingested.data.end_dates = [2011.75, 2012.76]
    assert not example_timeseries_ingested.timeseries_is_annual_grid(year_type=constants.YearType.GLACIOLOGICAL)


def test_convert_timeseries_to_longterm_trend(example_timeseries_ingested):
    example_timeseries_converted = example_timeseries_ingested.convert_timeseries_to_longterm_trend()
    assert len(example_timeseries_converted.data.changes) == 1
    assert np.array_equal(example_timeseries_converted.data.changes,
                          np.array([example_timeseries_ingested.data.changes.sum()]))
    assert np.array_equal(example_timeseries_converted.data.start_dates,
                          np.array([example_timeseries_ingested.data.start_dates[0]]))
    assert np.array_equal(example_timeseries_converted.data.end_dates,
                          np.array([example_timeseries_ingested.data.end_dates[1]]))


def test_convert_timeseries_to_longterm_trend_errors(example_timeseries_ingested):
    example_timeseries_converted = example_timeseries_ingested.convert_timeseries_to_longterm_trend()
    assert len(example_timeseries_converted.data.changes) == 1
    assert np.array_equal(example_timeseries_converted.data.changes,
                          np.array([example_timeseries_ingested.data.changes.sum()]))
    assert np.array_equal(example_timeseries_converted.data.errors,
                          np.array([np.sqrt(np.nansum(example_timeseries_ingested.data.errors**2)) / len(
                              example_timeseries_ingested.data.errors)]))


def test_apply_area_change(example_timeseries_ingested):
    timeseries_area_change = example_timeseries_ingested.apply_area_change(rgi_area_version=6, apply_change=True)
    assert not np.array_equal(example_timeseries_ingested.data.changes, np.array(timeseries_area_change.data.changes))
    assert timeseries_area_change.data.changes[-1] > 5.0
    assert timeseries_area_change.area_change_applied


def test_apply_area_change_convert_to_gt_equals_same(example_timeseries_ingested):
    timeseries_area_change = example_timeseries_ingested.apply_area_change(rgi_area_version=6, apply_change=True)

    # converting to gt should now give us the same result using the different areas
    # 1 convert the mwe without area change to Gt
    glacier_area = example_timeseries_ingested.region.rgi6_area
    gt_no_area_c = meters_water_equivalent_to_gigatonnes([example_timeseries_ingested.data.changes[0]],
                                                         area_km2=glacier_area)
    # 2 convert the mwe with area change to Gt, using the ahjusted area
    t_0 = timeseries_area_change.region.area_change_reference_year
    area_change = timeseries_area_change.region.area_change
    t_i = (timeseries_area_change.data.start_dates[0] + timeseries_area_change.data.end_dates[0]) / 2
    adjusted_area = glacier_area + (t_i - t_0) * (area_change / 100) * glacier_area
    gt_area_c = meters_water_equivalent_to_gigatonnes([timeseries_area_change.data.changes[0]], area_km2=adjusted_area)
    # this should now give the same result in Gt
    assert gt_no_area_c == gt_area_c


def test_apply_area_change_and_remove(example_timeseries_ingested):
    timeseries_area_change = example_timeseries_ingested.apply_area_change(rgi_area_version=6, apply_change=True)
    timeseries_area_change_removed = timeseries_area_change.apply_area_change(rgi_area_version=6, apply_change=False)
    assert np.array_equal(example_timeseries_ingested.data.changes,
                          np.array(timeseries_area_change_removed.data.changes))
    assert timeseries_area_change.area_change_applied
    assert not timeseries_area_change_removed.area_change_applied


def test_apply_area_change_and_wrong_unit(example_timeseries_ingested):
    example_timeseries_ingested.unit = "gt"
    with pytest.raises(AssertionError):
        example_timeseries_ingested.apply_area_change(rgi_area_version=6, apply_change=True)


def test_apply_area_change_when_already_applied(example_timeseries_ingested):
    timeseries_area_change = example_timeseries_ingested.apply_area_change(rgi_area_version=6, apply_change=True)
    with pytest.raises(AssertionError):
        timeseries_area_change.apply_area_change(rgi_area_version=6, apply_change=True)


def test_remove_area_change_when_already_removed(example_timeseries_ingested):
    assert not example_timeseries_ingested.area_change_applied
    with pytest.raises(AssertionError):
        example_timeseries_ingested.apply_area_change(rgi_area_version=6, apply_change=False)


def test_raises_assertion_error_when_converting_to_gt_with_area_change_applied(example_timeseries_ingested):
    timeseries_area_change = example_timeseries_ingested.apply_area_change(rgi_area_version=6, apply_change=True)
    with pytest.raises(AssertionError):
        timeseries_area_change.convert_timeseries_to_unit_gt()


def test_reduce_to_date_window(example_timeseries_ingested):
    reduced_timeseries = example_timeseries_ingested.reduce_to_date_window(start_date=2010.0, end_date=2010.2)
    assert np.array_equal(reduced_timeseries.data.changes, example_timeseries_ingested.data.changes[:-1])
    assert np.array_equal(reduced_timeseries.data.errors, example_timeseries_ingested.data.errors[:-1])
    assert np.array_equal(reduced_timeseries.data.start_dates, example_timeseries_ingested.data.start_dates[:-1])
    reduced_timeseries = example_timeseries_ingested.reduce_to_date_window(start_date=2010.2, end_date=2010.5)
    assert np.array_equal(reduced_timeseries.data.changes, example_timeseries_ingested.data.changes[1:])
    assert np.array_equal(reduced_timeseries.data.errors, example_timeseries_ingested.data.errors[1:])
    assert np.array_equal(reduced_timeseries.data.end_dates, example_timeseries_ingested.data.end_dates[1:])
