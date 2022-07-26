from glambie.const.data_groups import GlambieDataGroups


def test_get_glambie_data_group_by_name():
    region = GlambieDataGroups.get_data_group_by_name('altimetry')
    assert region.long_name == 'Altimetry'
    assert region.name == 'altimetry'
