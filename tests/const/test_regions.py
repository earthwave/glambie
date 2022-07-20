from glambie.const.regions import Regions


def test_get_region_by_id():
    region = Regions.get_region_by_id(6)
    assert region.rgi_id == 6
    assert region.name == 'iceland'


def test_get_region_by_name():
    region = Regions.get_region_by_name('iceland')
    assert region.name == 'iceland'
    assert region.rgi_id == 6
