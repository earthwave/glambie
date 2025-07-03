from glambie.const.regions import REGIONS, REGIONS_BY_ID, REGIONS_BY_SHORT_NAME
import numpy as np
import pytest


def test_get_region_by_short_name():
    region = REGIONS_BY_SHORT_NAME['ISL']
    assert region.name == 'iceland'


def test_get_region_by_id():
    region = REGIONS_BY_ID[6]
    assert region.name == 'iceland'


def test_get_region_by_name():
    region = REGIONS['iceland']
    assert region.name == 'iceland'
    assert region.rgi_id == 6


@pytest.mark.parametrize("rgi", [6, 7])
def test_get_adjusted_area(rgi):
    region = REGIONS['new_zealand']
    # no change expected for reference year
    adjusted_area_for_reference_year = region.get_adjusted_area(start_date=region.area_change_reference_year,
                                                                end_date=region.area_change_reference_year,
                                                                rgi_area_version=rgi)
    expected_result = region.rgi6_area if rgi == 6 else region.rgi7_area
    assert adjusted_area_for_reference_year == expected_result

    # add two years to reference year and adjust area
    adjusted_area_2_years = region.get_adjusted_area(start_date=region.area_change_reference_year,
                                                     end_date=region.area_change_reference_year + 2, 
                                                     rgi_area_version=rgi)
    assert adjusted_area_2_years < expected_result  # area should now have gotten smaller
    expected_value = expected_result + 1 * (region.area_change / 100) * expected_result  # calcualate expected value
    assert adjusted_area_2_years == expected_value

    # reference year +4 years is expected to have double of the change than +2 years (as adjustement is assumed linear)
    adjusted_area_4_years = region.get_adjusted_area(start_date=region.area_change_reference_year,
                                                     end_date=region.area_change_reference_year + 4, 
                                                     rgi_area_version=rgi)
    np.testing.assert_almost_equal(2 * (adjusted_area_2_years - expected_result),
                                   (adjusted_area_4_years - expected_result))
