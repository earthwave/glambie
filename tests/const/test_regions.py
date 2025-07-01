from glambie.const.regions import REGIONS, REGIONS_BY_ID, REGIONS_BY_SHORT_NAME
import numpy as np


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


def test_get_adjusted_area():
    region = REGIONS['iceland']
    # no change expected for reference year
    adjusted_area_reference_year = region.get_adjusted_area(start_date=region.area_change_reference_year,
                                                            end_date=region.area_change_reference_year,
                                                            rgi_area_version=7)
    assert adjusted_area_reference_year == region.rgi6_area

    # add two years to reference year and adjust area
    adjusted_area_2_years = region.get_adjusted_area(start_date=region.area_change_reference_year,
                                                     end_date=region.area_change_reference_year + 2, rgi_area_version=7)
    assert adjusted_area_2_years < region.rgi6_area  # area should now have gotten smaller
    expected_value = region.rgi6_area + 1 * (region.area_change / 100) * region.rgi6_area  # calcualate expected value
    assert adjusted_area_2_years == expected_value

    # reference year +4 years is expected to have double of the change than +2 years (as adjustement is assumed linear)
    adjusted_area_4_years = region.get_adjusted_area(start_date=region.area_change_reference_year,
                                                     end_date=region.area_change_reference_year + 4, rgi_area_version=7)
    np.testing.assert_almost_equal(2 * (adjusted_area_2_years - region.rgi6_area),
                                   (adjusted_area_4_years - region.rgi6_area))
