from glambie.const.regions import regions


def test_get_region_by_id():
    region = regions['iceland']
    assert region.rgi_id == 6
    assert region.name == 'iceland'


def test_get_region_by_name():
    region = regions['iceland']
    assert region.name == 'iceland'
    assert region.rgi_id == 6
