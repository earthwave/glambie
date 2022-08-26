from glambie.util.conversion_helpers import gigatonnes_to_sea_level_rise
from glambie.util.conversion_helpers import gigatonnes_to_meters
from glambie.util.conversion_helpers import meters_to_gigatonnes
from glambie.util.conversion_helpers import meters_to_meters_water_equivalent


def test_meters_to_gigatonnes():
    test_variable_in_m = 20
    test_rgi_area_km2 = 1000
    assert meters_to_gigatonnes(test_variable_in_m, test_rgi_area_km2) == 17
    # if non-default ice density is used
    test_density_of_ice_in_gt_per_m3 = 800
    assert meters_to_gigatonnes(test_variable_in_m, test_rgi_area_km2, test_density_of_ice_in_gt_per_m3) == 16


def test_gigatonnes_to_meters():
    test_variable_in_gt = 17
    test_rgi_area_km2 = 1000
    assert gigatonnes_to_meters(test_variable_in_gt, test_rgi_area_km2) == 20
    # if non-default ice density is used
    test_density_of_ice_in_gt_per_m3 = 800
    assert gigatonnes_to_meters(test_variable_in_gt, test_rgi_area_km2, test_density_of_ice_in_gt_per_m3) == 21.25


def test_meters_to_meters_water_equivalent():
    test_variable_in_m = 20
    assert meters_to_meters_water_equivalent(test_variable_in_m) == (20 / 997) * 850  # Is this ok? round() instead?
    # if non-default ice density is used
    test_density_of_ice_in_gt_per_m3 = 800
    assert meters_to_meters_water_equivalent(test_variable_in_m,
                                             density_of_ice_in_gt_per_m3=test_density_of_ice_in_gt_per_m3) == (
                                                 20 / 997) * 800
    # if non-default water density is used
    test_density_of_water_in_gt_per_m3 = 950
    assert meters_to_meters_water_equivalent(test_variable_in_m,
                                             density_of_water_in_gt_per_m3=test_density_of_water_in_gt_per_m3) == (
                                                 20 / 950) * 850


def test_gigatonnes_to_sea_level_rise():
    test_variable_in_gt = 50
    assert gigatonnes_to_sea_level_rise(test_variable_in_gt) == abs(50 / (3.625e8 * 1e6))
    # if non-default ocean area is used
    test_ocean_area = 3.8e8
    assert gigatonnes_to_sea_level_rise(test_variable_in_gt, ocean_area=test_ocean_area) == abs(50 / (3.8e8 * 1e6))
