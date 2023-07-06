from dataclasses import dataclass


@dataclass
class RGIRegion():
    rgi_id: int
    name: str
    long_name: str
    short_name: str
    rgi5_area: float
    rgi6_area: float
    rgi7_area: float
    area_uncertainty_percentage: float  # area uncertainty would be area_uncertainty_percentage * area
    area_change: float  # per year
    area_change_reference_year: int
    glaciological_year_start: float  # decimal of when the glaciological year starts, e.g. 0.75 would be October

    def __str__(self):
        return str(self.rgi_id) + '; ' + self.name + '; ' + self.long_name

    def __hash__(self):  # Make hashable
        return hash(self.name)


REGIONS = {
    'global': RGIRegion(
        rgi_id=0,
        name='global', long_name='Global', short_name='N/A',
        rgi5_area=705569, rgi6_area=705644, rgi7_area=None,
        area_uncertainty_percentage=None,
        area_change=None,
        area_change_reference_year=None,
        glaciological_year_start=0),

    'alaska': RGIRegion(
        rgi_id=1,
        name='alaska', long_name='Alaska', short_name='ALA',
        rgi5_area=86725, rgi6_area=86725, rgi7_area=None,
        area_uncertainty_percentage=0.05,  # 5% defined in GlamBIE Assessment Algorithm
        area_change=-0.48,
        area_change_reference_year=2009,
        glaciological_year_start=0.75),

    'western_canada_us': RGIRegion(
        rgi_id=2,
        name='western_canada_us', long_name='Western Canada & US', short_name='WNA',
        rgi5_area=14556, rgi6_area=14524, rgi7_area=None,
        area_uncertainty_percentage=0.05,
        area_change=-0.54,
        area_change_reference_year=2006,
        glaciological_year_start=0.75),

    'arctic_canada_north': RGIRegion(
        rgi_id=3,
        name='arctic_canada_north', long_name='Arctic Canada North', short_name='ACN',
        rgi5_area=105128, rgi6_area=105111, rgi7_area=None,
        area_uncertainty_percentage=0.05,
        area_change=-0.07,
        area_change_reference_year=2000,
        glaciological_year_start=0.75),

    'arctic_canada_south': RGIRegion(
        rgi_id=4,
        name='arctic_canada_south', long_name='Arctic Canada South', short_name='ACS',
        rgi5_area=40888, rgi6_area=40888, rgi7_area=None,
        area_uncertainty_percentage=0.05,
        area_change=-0.08,
        area_change_reference_year=2000,
        glaciological_year_start=0.75),

    'greenland_periphery': RGIRegion(
        rgi_id=5,
        name='greenland_periphery', long_name='Greenland Periphery', short_name='GRL',
        rgi5_area=89717, rgi6_area=89717, rgi7_area=None,
        area_uncertainty_percentage=0.05,
        area_change=-0.82,
        area_change_reference_year=2001,
        glaciological_year_start=0.75),

    'iceland': RGIRegion(
        rgi_id=6,
        name='iceland', long_name='Iceland',
        rgi5_area=11060, rgi6_area=11060, rgi7_area=None, short_name='ISL',
        area_uncertainty_percentage=0.05,  # 5% defined in GlamBIE Assessment Algorithm
        area_change=-0.36,
        area_change_reference_year=2000,
        glaciological_year_start=0.75),

    'svalbard': RGIRegion(
        rgi_id=7,
        name='svalbard', long_name='Svalbard & Jan Mayen', short_name='SJM',
        rgi5_area=33959, rgi6_area=33959, rgi7_area=None,
        area_uncertainty_percentage=0.05,  # 5% defined in GlamBIE Assessment Algorithm
        area_change=-0.26,
        area_change_reference_year=2001,
        glaciological_year_start=0.75),

    'scandinavia': RGIRegion(
        rgi_id=8,
        name='scandinavia', long_name='Scandinavia', short_name='SCA',
        rgi5_area=2851, rgi6_area=2949, rgi7_area=None,
        area_uncertainty_percentage=0.05,
        area_change=-0.27,
        area_change_reference_year=2002,
        glaciological_year_start=0.75),

    'russian_arctic': RGIRegion(
        rgi_id=9,
        name='russian_arctic', long_name='Russian Arctic', short_name='RUA',
        rgi5_area=51592, rgi6_area=51592, rgi7_area=None,
        area_uncertainty_percentage=0.05,
        area_change=-0.08,
        area_change_reference_year=2006,
        glaciological_year_start=0.75),

    'north_asia': RGIRegion(
        rgi_id=10,
        name='north_asia', long_name='North Asia', short_name='ASN',
        rgi5_area=2410, rgi6_area=2410, rgi7_area=None,
        area_uncertainty_percentage=0.05,
        area_change=-0.43,
        area_change_reference_year=2011,
        glaciological_year_start=0.75),

    'central_europe': RGIRegion(
        rgi_id=11,
        name='central_europe', long_name='Central Europe', short_name='CEU',
        rgi5_area=2075, rgi6_area=2092, rgi7_area=None,
        area_uncertainty_percentage=0.05,
        area_change=-0.93,
        area_change_reference_year=2003,
        glaciological_year_start=0.75),

    'caucasus_middle_east': RGIRegion(
        rgi_id=12,
        name='caucasus_middle_east', long_name='Caucasus & Middle East', short_name='CAU',
        rgi5_area=1295, rgi6_area=1307, rgi7_area=None,
        area_uncertainty_percentage=0.05,
        area_change=-0.53,
        area_change_reference_year=2001,
        glaciological_year_start=0.75),

    'central_asia': RGIRegion(
        rgi_id=13,
        name='central_asia', long_name='Central Asia', short_name='ASC',
        rgi5_area=49303, rgi6_area=49303, rgi7_area=None,
        area_uncertainty_percentage=0.05,  # 5% defined in GlamBIE Assessment Algorithm
        area_change=-0.18,
        area_change_reference_year=2003,
        glaciological_year_start=0.75),

    'south_asia_west': RGIRegion(
        rgi_id=14,
        name='south_asia_west', long_name='South Asia West', short_name='ASW',
        rgi5_area=33568, rgi6_area=33568, rgi7_area=None,
        area_uncertainty_percentage=0.05,
        area_change=-0.36,
        area_change_reference_year=2003,
        glaciological_year_start=0.75),

    'south_asia_east': RGIRegion(
        rgi_id=15,
        name='south_asia_east', long_name='South Asia East', short_name='ASE',
        rgi5_area=14734, rgi6_area=14734, rgi7_area=None,
        area_uncertainty_percentage=0.05,
        area_change=-0.47,
        area_change_reference_year=2003,
        glaciological_year_start=0.75),

    'low_latitudes': RGIRegion(
        rgi_id=16,
        name='low_latitudes', long_name='Low Latitudes', short_name='TRP',
        rgi5_area=2346, rgi6_area=2341, rgi7_area=None,
        area_uncertainty_percentage=0.05,
        area_change=-1.19,
        area_change_reference_year=2000,
        glaciological_year_start=0.0),

    'southern_andes': RGIRegion(
        rgi_id=17,
        name='southern_andes', long_name='Southern Andes', short_name='SAN',
        rgi5_area=29333, rgi6_area=29429, rgi7_area=None,
        area_uncertainty_percentage=0.05,
        area_change=-0.18,
        area_change_reference_year=2000,
        glaciological_year_start=0.25),

    'new_zealand': RGIRegion(
        rgi_id=18,
        name='new_zealand', long_name='New Zealand', short_name='NZL',
        rgi5_area=1162, rgi6_area=1162, rgi7_area=None,
        area_uncertainty_percentage=0.05,
        area_change=-0.69,
        area_change_reference_year=1978,
        glaciological_year_start=0.25),

    'antarctic_and_subantarctic': RGIRegion(
        rgi_id=19,
        name='antarctic_and_subantarctic',
        long_name='Antarctic and Subantarctic Islands', short_name='ANT',
        rgi5_area=132867, rgi6_area=132867, rgi7_area=None,
        area_uncertainty_percentage=0.05,
        area_change=-0.27,
        area_change_reference_year=1989,
        glaciological_year_start=0.25)
}

REGIONS_BY_ID = {r.rgi_id: r for r in REGIONS.values()}
REGIONS_BY_SHORT_NAME = {r.short_name: r for r in REGIONS.values()}
