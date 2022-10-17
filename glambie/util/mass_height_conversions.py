from typing import Iterable


def meters_to_gigatonnes(variables: Iterable, area: float, density_of_ice: float = 850) -> list:
    """Function to convert a list of measurements of surface elevation change in meters into ice mass in gigatonnes,
    using the area of a region and the density of ice.

    Parameters
    ----------
    variables : Iterable
        A list of measurements in meters
    area : float
        The area of a region in km2
    density_of_ice : float, optional
        The density of ice in Gt per m3, by default 850

    Returns
    -------
    A list of measurements in gigatonnes
    """
    return [_meters_to_gigatonnes(i, area, density_of_ice) for i in variables]


def gigatonnes_to_meters(variables: Iterable, area: float, density_of_ice: float = 850) -> list:
    """Function to convert a list of measurements of ice mass in gigatonnes into surface elevation change in meters,
    using the area of a region and the density of ice.

    Parameters
    ----------
    variables : Iterable
        A list of measurements in gigatonnes
    area : float
        The area of the region in km2
    density_of_ice : float, optional
        The density of ice in Gt per m3, by default 850

    Returns
    -------
    A list of measurements in meters
    """
    return [_gigatonnes_to_meters(i, area, density_of_ice) for i in variables]


def meters_to_meters_water_equivalent(variables: Iterable, density_of_water: float = 997,
                                      density_of_ice: float = 850) -> list:
    """Function to convert a list of measurements of surface elevation change in meters into meters water equivalent.

    Parameters
    ----------
    variables : Iterable
        A list of measurements in meters
    density_of_water : float, optional
        The density of water in Gt per m3, by default 997
    density_of_ice : float, optional
        The density of ice in Gt per m3, by default 850

    Returns
    -------
    A list of measurements in meters water equivalent
    """
    return [_meters_to_meters_water_equivalent(i, density_of_water, density_of_ice) for i in variables]


def meters_water_equivalent_to_meters(variables: Iterable, density_of_water: float = 997,
                                      density_of_ice: float = 850) -> list:
    """Function to convert a list of measurements of surface elevation change in meters water equivalent into meters.

    Parameters
    ----------
    variables : Iterable
        A list of measurements in meters water equivalent
    density_of_water : float, optional
        The density of water in Gt per m3, by default 997
    density_of_ice : float, optional
        The density of ice in Gt per m3, by default 850

    Returns
    -------
    A list of measurements in meters
    """
    return [_meters_water_equivalent_to_meters(i, density_of_water, density_of_ice) for i in variables]


def gigatonnes_to_meters_water_equivalent(variables: Iterable, area: float, density_of_water: float = 997) -> list:
    """Function to convert a list of measurements of ice mass loss in gigatonnes into meters water equivalent.

    Parameters
    ----------
    variables : Iterable
        A list of measurements in gigatonnes
    area : float
        The area of the region in km2
    density_of_water : float, optional
        The density of water in Gt per m3, by default 997

    Returns
    -------
    A list of measurements in meters water equivalent
    """
    return [_gigatonnes_to_meters_water_equivalent(i, area, density_of_water) for i in variables]


def gigatonnes_to_sea_level_rise(variables: Iterable, ocean_area: float = 3.625e8) -> list:
    """Function to convert a list of measurements of ice mass loss in gigatonnes into sea level rise (millimeters). We
    assume a value for the area of the ocean, and that all measured mass loss contributes to sea level change.

    Parameters
    ----------
    variables : Iterable
        A List of measurements in gigatonnes
    ocean_area : float, optional
        The assumed area of the ocean in km2, by default 3.625e8

    Returns
    -------
    A list of measurements in sea level rise (millimeters)
    """
    return [_gigatonnes_to_sea_level_rise(i, ocean_area) for i in variables]


def _meters_to_gigatonnes(variable: float, area: float, density_of_ice: float = 850) -> float:
    """Function to convert a measurement of surface elevation change in meters into ice mass in gigatonnes

    Parameters
    ----------
    variable : float
        The variable to be converted, with input units of meters
    area : float
        The area of the region in km2
    density_of_ice : float, optional
        The density of ice in Gt per m3, by default 850

    Returns:
    ----------
    Input variable converted into gigatonnes
    """
    return variable * density_of_ice * (area / 1e6)  # 1e6 to convert area from km2 to m2


def _gigatonnes_to_meters(variable: float, area: float, density_of_ice: float = 850) -> float:
    """Function to convert a measurement of ice mass in gigatonnes into surface elevation change in meters

    Parameters
    ----------
    variable : float
        The variable to be converted, with input units of gigatonnes
    area : float
        The area of the region in km2
    density_of_ice : float, optional
        The density of ice in Gt per m3, by default 850

    Returns:
    ----------
    Input variable converted into meters
    """
    return (1e6 * variable) / (area * density_of_ice)  # 1e6 to convert area from km2 to m2


def _meters_to_meters_water_equivalent(variable: float, density_of_water: float = 997,
                                       density_of_ice: float = 850) -> float:
    """Function to convert a measurement of surface elevation change from meters into meters water equivalent.

    Parameters
    ----------
    variable : float
        The variable to be converted, with input units of meters
    density_of_water : float, optional
        The density of water in Gt per m3, by default 997
    density_of_ice : float, optional
        The density of ice in Gt per m3, by default 850

    Returns
    -------
    Input variable converted into meters water equivalent
    """
    return (variable / density_of_water) * density_of_ice


def _meters_water_equivalent_to_meters(variable: float, density_of_water: float = 997,
                                       density_of_ice: float = 850) -> float:
    """Function to convert a measurement of surface elevation change from meters water equivalent into meters.

    Parameters
    ----------
    variable : float
        The variable to be converted, with input units of mwe
    density_of_water: float, optional
        The density of water in Gt per m3, by default 997
    density_of_ice : float, optional
        The density of ice in Gt per m3, by default 850

    Returns
    -------
    Input variable converted into meters
    """
    return (variable * density_of_water) / density_of_ice


def _gigatonnes_to_meters_water_equivalent(variable: float, area: float, density_of_water: float = 997) -> float:
    """Function to convert a measurement of ice mass loss in gigatonnes into meters water equivalent

    Parameters
    ----------
    variable : float
        The variable to be converted, with input units of Gt
    area : float
        The area of the region in km2
    density_of_water : float, optional
        The density of water in Gt per m3, by default 997

    Returns
    -------
    Input variable converted into meters water equivalent
    """
    return (1e6 * variable) / (area * density_of_water)  # 1e6 to convert area from km2 to m2


def _gigatonnes_to_sea_level_rise(variable: float, ocean_area: float = 3.625e8) -> float:
    """Function to convert a measurement of ice mass loss in gigatonnes into sea level rise (millimeters).

    Parameters
    ----------
    variable : float
        The variable to be converted, with input units of gigatonnes
    ocean_area : float, optional
        The assumed area of the ocean in km2, by default 3.625e8

    Returns
    ----------
    Input variable converted into sea level rise (millimeters)
    """
    return abs(variable / ocean_area) * 1e6  # 1e6 to convert area from km2 to m2
