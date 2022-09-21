from dataclasses import dataclass


@dataclass
class GlambieDataGroup():
    name: str
    long_name: str  # might add some more here later


GLAMBIE_DATA_GROUPS = {
    'altimetry': GlambieDataGroup(name='altimetry', long_name='Altimetry'),
    'demdiff': GlambieDataGroup(name='demdiff', long_name='DEM differencing'),
    'gravimetry': GlambieDataGroup(name='gravimetry', long_name='Gravimetry'),
    # Here, 'Glaciological' refers to measurements of the glacier's surface from seasonal or annual in-situ campaigns.
    'glaciological': GlambieDataGroup(name='glaciological', long_name='Glaciological'),
    'combined': GlambieDataGroup(name='combined', long_name='Combination of methods')
}
