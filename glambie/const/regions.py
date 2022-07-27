from dataclasses import dataclass


@dataclass
class RGIRegion():
    rgi_id: int
    name: str
    long_name: str
    rgi6_area: float
    rgi7_area: float
    area_change: float

    def __str__(self):
        return str(self.rgi_id) + '; ' + self.name + '; ' + self.long_name


class MetaRegions(type):

    def __str__(cls):
        string = ''
        for region in cls.regions:
            string = string + str(region) + '\n'
        return string


class Regions(metaclass=MetaRegions):
    """Containing all RGI regions for Glambie
    """
    regions = [     # probably read this from a file in future, currently containing the test regions
        RGIRegion(rgi_id=1, name='alaska', long_name='Alaska', rgi6_area=86725, rgi7_area=86725, area_change=-0.48),
        RGIRegion(rgi_id=6, name='iceland', long_name='Iceland', rgi6_area=11060, rgi7_area=11060, area_change=-0.36),
        RGIRegion(rgi_id=7, name='svalbard', long_name='Svalbard & Jan Mayen', rgi6_area=33959, rgi7_area=33959,\
                  area_change=-0.26)
    ]

    @staticmethod
    def get_region_by_id(rgi_id: int):
        region_result = [i for i in Regions.regions if i.rgi_id == rgi_id]
        if len(region_result) == 0:  # id not found
            return None
        else:
            return region_result[0]

    @staticmethod
    def get_region_by_name(name: str):
        region_result = [i for i in Regions.regions if i.name == name]
        if len(region_result) == 0:  # name not found
            return None
        else:
            return region_result[0]
