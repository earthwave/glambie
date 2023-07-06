from glambie.const.regions import REGIONS, REGIONS_BY_ID, REGIONS_BY_SHORT_NAME


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
