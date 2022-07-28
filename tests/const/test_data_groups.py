from glambie.const.data_groups import GLAMBIE_DATA_GROUPS


def test_get_glambie_data_group_by_name():
    region = GLAMBIE_DATA_GROUPS['altimetry']
    assert region.long_name == 'Altimetry'
    assert region.name == 'altimetry'
