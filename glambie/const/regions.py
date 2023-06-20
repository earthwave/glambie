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
