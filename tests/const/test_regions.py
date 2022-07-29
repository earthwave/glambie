from glambie.const.regions import REGIONS, get_region_by_id


def test_get_region_by_id():
    region = REGIONS['iceland']
    assert get_region_by_id(6) == region


def test_get_region_by_name():
    region = REGIONS['iceland']
    assert region.name == 'iceland'
    assert region.rgi_id == 6
