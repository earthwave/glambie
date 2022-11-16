from typing import Iterable
from glambie.const import constants


def meters_to_gigatonnes(variables: Iterable, area_km2: float,
                         density_of_ice: float = constants.DENSITY_OF_ICE_GT_PER_M3) -> list:
    """Function to convert a list of measurements of surface elevation change in meters into ice mass in gigatonnes,
    using the area of a region and the density of ice.

    Parameters
    ----------
    variables : Iterable
        A list of measurements in meters
    area_km2 : float
        The area of a region in km2
    density_of_ice : float, optional
        The density of ice in Gt per m3, by default constants.DENSITY_OF_ICE_GT_PER_M3

    Returns
    -------
    A list of measurements in gigatonnes
    """
    return [i * density_of_ice * (area_km2 / 1e6) for i in variables]  # 1e6 to convert area from km2 to m2


def gigatonnes_to_meters(variables: Iterable, area_km2: float,
                         density_of_ice: float = constants.DENSITY_OF_ICE_GT_PER_M3) -> list:
    """Function to convert a list of measurements of ice mass in gigatonnes into surface elevation change in meters,
    using the area of a region and the density of ice.

    Parameters
    ----------
    variables : Iterable
        A list of measurements in gigatonnes
    area_km2 : float
        The area of the region in km2
    density_of_ice : float, optional
        The density of ice in Gt per m3, by default constants.DENSITY_OF_ICE_GT_PER_M3

    Returns
    -------
    A list of measurements in meters
    """
    return [(1e6 * variable) / (area_km2 * density_of_ice) for variable in variables]


def meters_to_meters_water_equivalent(variables: Iterable,
                                      density_of_water: float = constants.DENSITY_OF_WATER_GT_PER_M3,
                                      density_of_ice: float = constants.DENSITY_OF_ICE_GT_PER_M3) -> list:
    """Function to convert a list of measurements of surface elevation change in meters into meters water equivalent.

    Parameters
    ----------
    variables : Iterable
        A list of measurements in meters
    density_of_water : float, optional
        The density of water in Gt per m3, by default constants.DENSITY_OF_WATER_GT_PER_M3
    density_of_ice : float, optional
        The density of ice in Gt per m3, by default constants.DENSITY_OF_ICE_GT_PER_M3

    Returns
    -------
    A list of measurements in meters water equivalent
    """
    return [(variable / density_of_water) * density_of_ice for variable in variables]


def meters_water_equivalent_to_meters(variables: Iterable,
                                      density_of_water: float = constants.DENSITY_OF_WATER_GT_PER_M3,
                                      density_of_ice: float = constants.DENSITY_OF_ICE_GT_PER_M3) -> list:
    """Function to convert a list of measurements of surface elevation change in meters water equivalent into meters.

    Parameters
    ----------
    variables : Iterable
        A list of measurements in meters water equivalent
    density_of_water : float, optional
        The density of water in Gt per m3, by default constants.DENSITY_OF_WATER_GT_PER_M3
    density_of_ice : float, optional
        The density of ice in Gt per m3, by default constants.DENSITY_OF_ICE_GT_PER_M3

    Returns
    -------
    A list of measurements in meters
    """
    return [(variable * density_of_water) / density_of_ice for variable in variables]


def meters_water_equivalent_to_gigatonnes(variables: Iterable, area_km2: float,
                                          density_of_water: float = constants.DENSITY_OF_WATER_GT_PER_M3) -> list:
    """Function to convert a list of measurements of ice mass loss in meters water equivalent to gigatonnes.

    Parameters
    ----------
    variables : Iterable
        A list of measurements in meters water equivalent
    area_km2 : float
        The area of the region in km2
    density_of_water : float, optional
        The density of water in Gt per m3, by default constants.DENSITY_OF_WATER_GT_PER_M3

    Returns
    -------
    A list of measurements in gigatonnes
    """
    return [i * density_of_water * (area_km2 / 1e6) for i in variables]  # 1e6 to convert area from km2 to m2


def gigatonnes_to_meters_water_equivalent(variables: Iterable, area_km2: float,
                                          density_of_water: float = constants.DENSITY_OF_WATER_GT_PER_M3) -> list:
    """Function to convert a list of measurements of ice mass loss in gigatonnes into meters water equivalent.

    Parameters
    ----------
    variables : Iterable
        A list of measurements in gigatonnes
    area_km2 : float
        The area of the region in km2
    density_of_water : float, optional
        The density of water in Gt per m3, by default constants.DENSITY_OF_WATER_GT_PER_M3

    Returns
    -------
    A list of measurements in meters water equivalent
    """
    return [(1e6 * variable) / (area_km2 * density_of_water) for variable in variables]


def gigatonnes_to_sea_level_rise(variables: Iterable, ocean_area_km2: float = constants.OCEAN_AREA_IN_KM2) -> list:
    """Function to convert a list of measurements of ice mass loss in gigatonnes into sea level rise (millimeters). We
    assume a value for the area of the ocean, and that all measured mass loss contributes to sea level change.

    Parameters
    ----------
    variables : Iterable
        A List of measurements in gigatonnes
    ocean_area_km2 : float, optional
        The assumed area of the ocean in km2, by default constants.OCEAN_AREA_IN_KM2

    Returns
    -------
    A list of measurements in sea level rise (millimeters)
    """
    return [abs(variable / ocean_area_km2) * 1e6 for variable in variables]  # 1e6 to convert area from km2 to m2
