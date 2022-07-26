from dataclasses import dataclass


@dataclass
class GlambieDataGroup():
    name: str
    long_name: str  # might add some more here later


class GlambieDataGroups():
    """Containing all Method groups for Glambie
    """
    data_groups = [
        GlambieDataGroup(name='altimetry', long_name='Altimetry'),
        GlambieDataGroup(name='demdiff', long_name='DEM differencing'),
        GlambieDataGroup(name='gravimetry', long_name='Gravimetry'),
        GlambieDataGroup(name='combined', long_name='Combination of methods')
    ]

    @staticmethod
    def get(name: str):
        return GlambieDataGroups.get_data_group_by_name(name)

    @staticmethod
    def get_data_group_by_name(name: str):
        result = [i for i in GlambieDataGroups.data_groups if i.name == name]
        if len(result) == 0:  # name not found
            return None
        else:
            return result[0]
