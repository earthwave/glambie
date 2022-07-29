from glambie.const.regions import REGIONS


def test_get_region_by_id():
    # @SOPHIE TODO: WRITE TEST
    pass


def test_get_region_by_name():
    region = REGIONS['iceland']
    assert region.name == 'iceland'
    assert region.rgi_id == 6
