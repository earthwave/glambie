from glambie.util.mass_height_conversions import _meters_to_gigatonnes
from glambie.util.mass_height_conversions import _gigatonnes_to_meters
from glambie.util.mass_height_conversions import _meters_to_meters_water_equivalent
from glambie.util.mass_height_conversions import _meters_water_equivalent_to_meters
from glambie.util.mass_height_conversions import _gigatonnes_to_sea_level_rise
from glambie.util.mass_height_conversions import _gigatonnes_to_meters_water_equivalent
from glambie.util.mass_height_conversions import _meters_water_equivalent_to_gigatonnes

from glambie.util.mass_height_conversions import meters_to_gigatonnes
from glambie.util.mass_height_conversions import gigatonnes_to_meters
from glambie.util.mass_height_conversions import meters_to_meters_water_equivalent
from glambie.util.mass_height_conversions import meters_water_equivalent_to_meters
from glambie.util.mass_height_conversions import gigatonnes_to_sea_level_rise
from glambie.util.mass_height_conversions import gigatonnes_to_meters_water_equivalent
from glambie.util.mass_height_conversions import meters_water_equivalent_to_gigatonnes


def test_meters2gigatonnes():
    test_variable_in_m = 20
    test_rgi_area_km2 = 1000
    assert _meters_to_gigatonnes(20, 1000) == 17
    # if non-default ice density is used
    test_density_of_ice_in_gt_per_m3 = 800
    assert _meters_to_gigatonnes(test_variable_in_m, test_rgi_area_km2, test_density_of_ice_in_gt_per_m3) == 16


def test_gigatonnes2meters():
    test_variable_in_gt = 17
    test_rgi_area_km2 = 1000
    assert _gigatonnes_to_meters(test_variable_in_gt, test_rgi_area_km2) == 20
    # if non-default ice density is used
    test_density_of_ice_in_gt_per_m3 = 800
    assert _gigatonnes_to_meters(test_variable_in_gt, test_rgi_area_km2,
                                 test_density_of_ice_in_gt_per_m3) == 21.25


def test_meters2mwe():
    test_variable_in_m = 20
    assert _meters_to_meters_water_equivalent(test_variable_in_m) == (20 / 997) * 850
    # if non-default ice density is used
    test_density_of_ice = 800
    assert _meters_to_meters_water_equivalent(test_variable_in_m,
                                              density_of_ice=test_density_of_ice) == (20 / 997) * 800
    # if non-default water density is used
    test_density_of_water = 950
    assert _meters_to_meters_water_equivalent(test_variable_in_m,
                                              density_of_water=test_density_of_water) == (20 / 950) * 850


def test_mwe2meters():
    test_variable_in_mwe = 20
    assert _meters_water_equivalent_to_meters(test_variable_in_mwe) == (20 * 997) / 850
    # if non-default ice density is used
    test_density_of_ice = 800
    assert _meters_water_equivalent_to_meters(test_variable_in_mwe,
                                              density_of_ice=test_density_of_ice) == (20 * 997) / 800
    # if non-default water density is used
    test_density_of_water = 950
    assert _meters_water_equivalent_to_meters(test_variable_in_mwe,
                                              density_of_water=test_density_of_water) == (20 * 950) / 850


def test_gigatonnes2mwe():
    test_variable_in_gt = 50
    test_area = 1000
    assert _gigatonnes_to_meters_water_equivalent(test_variable_in_gt, test_area) == (1e6 * 50) / (1000 * 997)
    test_density_of_water = 950
    assert _gigatonnes_to_meters_water_equivalent(
        test_variable_in_gt, test_area, density_of_water=test_density_of_water) == (1e6 * 50) / (1000 * 950)


def test_mwe2gt():
    area = 10
    mwe = 0.2

    # circular test: should give same as first converting to meters and then to Gt
    m = _meters_water_equivalent_to_meters(mwe)
    gt = _meters_to_gigatonnes(m, area_km=area)
    assert _meters_water_equivalent_to_gigatonnes(mwe, area_km2=area) == gt


def test_gigatonnes2slr():
    test_variable_in_gt = 50
    assert _gigatonnes_to_sea_level_rise(test_variable_in_gt) == abs(50 / 3.625e8) * 1e6
    # if non-default ocean area is used
    test_ocean_area = 3.8e8
    assert _gigatonnes_to_sea_level_rise(test_variable_in_gt,
                                         ocean_area_km2=test_ocean_area) == abs(50 / 3.8e8) * 1e6


def test_meters_to_gigatonnes():
    meters_list = [20, 30]
    assert meters_to_gigatonnes(meters_list, 1000) == [17, 25.5]


def test_gigatonnes_to_meters():
    gigatonnes_list = [17, 25.5]
    assert gigatonnes_to_meters(gigatonnes_list, 1000) == [20, 30]


def test_meters_to_meters_water_equivalent():
    meters_list = [20, 30]
    assert meters_to_meters_water_equivalent(meters_list) == [(20 / 997) * 850, (30 / 997) * 850]


def test_meters_water_equivalent_to_meters():
    mwe_list = [20, 30]
    assert meters_water_equivalent_to_meters(mwe_list) == [(20 * 997) / 850, (30 * 997) / 850]


def test_gigatonnes_to_meters_water_equivalent():
    gigatonnes_list = [50, 60]
    assert gigatonnes_to_meters_water_equivalent(gigatonnes_list,
                                                 1000) == [(1e6 * 50) / (1000 * 997), (1e6 * 60) / (1000 * 997)]


def test_gigatonnes_to_sea_level_rise():
    gigatonnes_list = [50, 60]
    assert gigatonnes_to_sea_level_rise(gigatonnes_list) == [abs(50 / 3.625e8) * 1e6, abs(60 / 3.625e8) * 1e6]


def test_meters_water_equivalent_to_gigatonnes():
    area = 10
    mwe = [0.2, 0.4, 0.6, 0.006]

    # circular test: should give same as first converting to meters and then to Gt
    m = meters_water_equivalent_to_meters(mwe)
    gt = meters_to_gigatonnes(m, area=area)
    assert meters_water_equivalent_to_gigatonnes(mwe, area=area) == gt
