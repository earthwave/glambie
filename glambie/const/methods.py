from dataclasses import dataclass


@dataclass
class GlambieMethod():
    name: str
    long_name: str  # might add some more here later


class GlambieMethods():
    """Containing all Method groups for Glambie
    """
    methods = [
        GlambieMethod(name='altimetry', long_name='Altimetry'),
        GlambieMethod(name='demdiff', long_name='DEM differencing'),
        GlambieMethod(name='gravimetry', long_name='Gravimetry'),
        GlambieMethod(name='combined', long_name='Combination of methods')
    ]

    @staticmethod
    def get_method_by_name(name: str):
        result = [i for i in GlambieMethods.methods if i.name == name]
        if len(result) == 0:  # name not found
            return None
        else:
            return result[0]
