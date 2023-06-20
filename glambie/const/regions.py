from dataclasses import dataclass


@dataclass
class RGIRegion():
    rgi_id: int
    name: str
    long_name: str
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
    'alaska': RGIRegion(rgi_id=1, name='alaska', long_name='Alaska',
                        rgi5_area=86725, rgi6_area=86725, rgi7_area=86725,
                        area_uncertainty_percentage=0.05,  # 5% defined in GlamBIE Assessment Algorithm
                        area_change=-0.48,
                        area_change_reference_year=2009,
                        glaciological_year_start=0.75),
    'western_canada_us': RGIRegion(rgi_id=2, name='western_canada_us', long_name='Western Canada & US',
                                   rgi5_area=14556, rgi6_area=14524, rgi7_area=14524,
                                   area_uncertainty_percentage=0.05,
                                   area_change=-0.54,
                                   area_change_reference_year=2006,
                                   glaciological_year_start=0.75),
    'arctic_canada_north': RGIRegion(rgi_id=3, name='arctic_canada_north', long_name='Arctic Canada North',
                                     rgi5_area=105128, rgi6_area=105111, rgi7_area=105111,
                                     area_uncertainty_percentage=0.05,
                                     area_change=-0.07,
                                     area_change_reference_year=2000,
                                     glaciological_year_start=0.75),
    'arctic_canada_south': RGIRegion(rgi_id=4, name='arctic_canada_south', long_name='Arctic Canada South',
                                     rgi5_area=40888, rgi6_area=40888, rgi7_area=40888,
                                     area_uncertainty_percentage=0.05,
                                     area_change=-0.08,
                                     area_change_reference_year=2000,
                                     glaciological_year_start=0.75),
    'greenland_periphery': RGIRegion(rgi_id=5, name='greenland_periphery', long_name='Greenland Periphery',
                                     rgi5_area=89717, rgi6_area=89717, rgi7_area=89717,
                                     area_uncertainty_percentage=0.05,
                                     area_change=-0.82,
                                     area_change_reference_year=2001,
                                     glaciological_year_start=0.75),
    'iceland': RGIRegion(rgi_id=6, name='iceland', long_name='Iceland',
                         rgi5_area=11060, rgi6_area=11060, rgi7_area=11060,
                         area_uncertainty_percentage=0.05,  # 5% defined in GlamBIE Assessment Algorithm
                         area_change=-0.36,
                         area_change_reference_year=2000,
                         glaciological_year_start=0.75),
    'svalbard': RGIRegion(rgi_id=7, name='svalbard', long_name='Svalbard & Jan Mayen',
                          rgi5_area=33959, rgi6_area=33959, rgi7_area=33959,
                          area_uncertainty_percentage=0.05,  # 5% defined in GlamBIE Assessment Algorithm
                          area_change=-0.26,
                          area_change_reference_year=2001,
                          glaciological_year_start=0.75),
    'scandinavia': RGIRegion(rgi_id=8, name='scandinavia', long_name='Scandinavia',
                             rgi5_area=2851, rgi6_area=2949, rgi7_area=2949,
                             area_uncertainty_percentage=0.05,
                             area_change=-0.27,
                             area_change_reference_year=2002,
                             glaciological_year_start=0.75),
    'russian_arctic': RGIRegion(rgi_id=9, name='russian_arctic', long_name='Russian Arctic',
                                rgi5_area=51592, rgi6_area=51592, rgi7_area=51592,
                                area_uncertainty_percentage=0.05,
                                area_change=-0.08,
                                area_change_reference_year=2006,
                                glaciological_year_start=0.75),
    'north_asia': RGIRegion(rgi_id=10, name='north_asia', long_name='North Asia',
                            rgi5_area=2410, rgi6_area=2410, rgi7_area=2410,
                            area_uncertainty_percentage=0.05,
                            area_change=-0.43,
                            area_change_reference_year=2011,
                            glaciological_year_start=0.75),
    'central_asia': RGIRegion(rgi_id=13, name='central_asia', long_name='Central Asia',
                              rgi5_area=49303, rgi6_area=49303, rgi7_area=49303,
                              area_uncertainty_percentage=0.05,  # 5% defined in GlamBIE Assessment Algorithm
                              area_change=-0.18,
                              area_change_reference_year=2003,
                              glaciological_year_start=0.75)}


def get_region_by_id(rgi_id: int) -> RGIRegion:
    """Returns region object that matches input ID
    """
    for key in REGIONS:
        if REGIONS[key].rgi_id == rgi_id:
            return REGIONS[key]
