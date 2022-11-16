from glambie.util.mass_height_conversions import meters_to_gigatonnes
from glambie.util.mass_height_conversions import gigatonnes_to_meters
from glambie.util.mass_height_conversions import meters_to_meters_water_equivalent
from glambie.util.mass_height_conversions import meters_water_equivalent_to_meters
from glambie.util.mass_height_conversions import gigatonnes_to_sea_level_rise
from glambie.util.mass_height_conversions import gigatonnes_to_meters_water_equivalent
from glambie.util.mass_height_conversions import meters_water_equivalent_to_gigatonnes
from glambie.const import constants


def test_meters_to_gigatonnes():
    meters_list = [20, 30]
    assert meters_to_gigatonnes(meters_list, 1000, density_of_ice=850) == [17, 25.5]


def test_gigatonnes_to_meters():
    gigatonnes_list = [17, 25.5]
    assert gigatonnes_to_meters(gigatonnes_list, 1000, density_of_ice=850) == [20, 30]


def test_meters_to_meters_water_equivalent():
    meters_list = [20, 30]
    density_of_ice = 852
    density_of_water = 998
    assert meters_to_meters_water_equivalent(meters_list, density_of_ice=density_of_ice,
                                             density_of_water=density_of_water) == [
        (20 / density_of_water) * density_of_ice, (30 / density_of_water) * density_of_ice]


def test_meters_water_equivalent_to_meters():
    mwe_list = [20, 30]
    density_of_ice = 852
    density_of_water = 998
    assert meters_water_equivalent_to_meters(mwe_list, density_of_ice=density_of_ice,
                                             density_of_water=density_of_water) == [
        (20 * density_of_water) / density_of_ice, (30 * density_of_water) / density_of_ice]


def test_gigatonnes_to_meters_water_equivalent():
    gigatonnes_list = [50, 60]
    density_of_water = 1006
    assert gigatonnes_to_meters_water_equivalent(gigatonnes_list, 1000, density_of_water=density_of_water) == [
        (1e6 * 50) / (1000 * density_of_water), (1e6 * 60) / (1000 * density_of_water)]


def test_gigatonnes_to_sea_level_rise():
    gigatonnes_list = [50, 60]
    area_ocean = 3.125e8
    assert gigatonnes_to_sea_level_rise(gigatonnes_list, ocean_area_km2=area_ocean) == [abs(
        50 / area_ocean) * 1e6, abs(60 / area_ocean) * 1e6]
    # now test with default parameter
    assert gigatonnes_to_sea_level_rise(gigatonnes_list) == [abs(
        50 / constants.OCEAN_AREA_IN_KM2) * 1e6, abs(60 / constants.OCEAN_AREA_IN_KM2) * 1e6]


def test_meters_water_equivalent_to_gigatonnes():
    area = 10
    mwe = [0.2, 0.4, 0.6, 0.006]

    # circular test: should give same as first converting to meters and then to Gt
    m = meters_water_equivalent_to_meters(mwe)
    gt = meters_to_gigatonnes(m, area_km2=area)
    assert meters_water_equivalent_to_gigatonnes(mwe, area_km2=area) == gt
