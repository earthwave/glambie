def meters_to_gigatonnes(meters_list: list, rgi_area_km2: float, density_of_ice_in_gt_per_m3: float = 850) -> list:
    """Function to convert a list of measurements of surface elevation change in meters into ice mass in gigatonnes,
    using the area of a region and the density of ice.

    Parameters
    ----------
    meters_list : list
        A list of measurements in meters
    rgi_area_km2 : float
        The area of a region in km2
    density_of_ice_in_gt_per_m3 : float, optional
        The density of ice in Gt per m3, by default 850

    Returns
    -------
    A list of measurements in gigatonnes
    """
    return [meter2gigatonne(i, rgi_area_km2, density_of_ice_in_gt_per_m3) for i in meters_list]


def gigatonnes_to_meters(gigatonnes_list: list, rgi_area_km2: float, density_of_ice_in_gt_per_m3: float = 850) -> list:
    """Function to convert a list of measurements of ice mass in gigatonnes into surface elevation change in meters,
    using the area of a region and the density of ice.

    Parameters
    ----------
    gigatonnes_list : list
        A list of measurements in gigatonnes
    rgi_area_km2 : float
        The area of the region in km2
    density_of_ice_in_gt_per_m3 : float, optional
        The density of ice in Gt per m3, by default 850

    Returns
    -------
    A list of measurements in meters
    """
    return [gigatonne2meter(i, rgi_area_km2, density_of_ice_in_gt_per_m3) for i in gigatonnes_list]


def meters_to_meters_water_equivalent(meters_list: list, density_of_water_in_gt_per_m3: float = 997,
                                      density_of_ice_in_gt_per_m3: float = 850) -> list:
    """Function to convert a list of measurements of surface elevation change in meters into meters water equivalent.

    Parameters
    ----------
    meters_list : list
        A list of measurements in meters
    density_of_water_in_Gt_per_m3 : float, optional
        The density of water in Gt per m3, by default 997
    density_of_ice_in_Gt_per_m3 : float, optional
        The density of ice in Gt per m3, by default 850

    Returns
    -------
    A list of measurements in meters water equivalent
    """
    return [meter2mwe(i, density_of_water_in_gt_per_m3, density_of_ice_in_gt_per_m3) for i in meters_list]


def meters_water_equivalent_to_meters(meters_water_equivalent_list: list, density_of_water_in_gt_per_m3: float = 997,
                                      density_of_ice_in_gt_per_m3: float = 850) -> list:
    """Function to convert a list of measurements of surface elevation change in meters water equivalent into meters.

    Parameters
    ----------
    meters_we_list : list
        A list of measurements in meters water equivalent
    density_of_water_in_gt_per_m3 : float, optional
        The density of waterr in Gt per m3, by default 997
    density_of_ice_in_gt_per_m3 : float, optional
        The density of ice in Gt per m3, by default 850

    Returns
    -------
    A list of measurements in meters
    """
    return [mwe2meter(i, density_of_water_in_gt_per_m3,
                      density_of_ice_in_gt_per_m3) for i in meters_water_equivalent_list]


def gigatonnes_to_sea_level_rise(gigatonnes_list: list, ocean_area: float = 3.625e8) -> list:
    """Function to convert a list of measurements of ice mass loss in gigatonnes into sea level rise (millimeters). We
    assume a value for the area of the ocean, and that all measured mass loss contributes to sea level change.

    Parameters
    ----------
    gigatonnes_list : list
        list of measurements in gigatonnes
    ocean_area : float, optional
        The assumed area of the ocean in km2, by default 3.625e8

    Returns
    -------
    A list of measurements in sea level rise (millimeters)
    """
    return [gigatonne2slr(i, ocean_area) for i in gigatonnes_list]


def meter2gigatonne(variable_in_m: float, rgi_area_km2: float, density_of_ice_in_gt_per_m3: float = 850) -> float:
    """Function to convert a measurement of surface elevation change in meters into ice mass in gigatonnes

    Parameters
    ----------
    variable_in_m : float
        The variable to be converted, with input units of meters
    rgi_area_km2 : float
        The area of the region in km2
    density_of_ice_in_gt_per_m3 : float, optional
        The density of ice in Gt per m3, by default 850

    Returns:
    ----------
    Input variable converted into gigatonnes
    """
    return variable_in_m * density_of_ice_in_gt_per_m3 * (rgi_area_km2 / 1e6)


def gigatonne2meter(variable_in_gt: float, rgi_area_km2: float, density_of_ice_in_gt_per_m3: float = 850) -> float:
    """Function to convert a measurement of ice mass in gigatonnes into surface elevation change in meters

    Parameters
    ----------
    variable_in_gt : float
        The variable to be converted, with input units of gigatonnes
    rgi_area_km2 : float
        The area of the region in km2
    density_of_ice_in_gt_per_m3 : float, optional
        The density of ice in Gt per m3, by default 850

    Returns:
    ----------
    Input variable converted into meters
    """
    return (1e6 * variable_in_gt) / (rgi_area_km2 * density_of_ice_in_gt_per_m3)


def meter2mwe(variable_in_m: float, density_of_water_in_gt_per_m3: float = 997,
              density_of_ice_in_gt_per_m3: float = 850) -> float:
    """Function to convert a measurement of surface elevation change from meters into meters water equivalent.

    Parameters
    ----------
    variable_in_m : float
        The variable to be converted, with input units of meters
    density_of_water_in_Gt_per_m3 : float, optional
        The density of water in Gt per m3, by default 997
    density_of_ice_in_Gt_per_m3 : float, optional
        The density of ice in Gt per m3, by default 850

    Returns
    -------
    Input variable converted into meters water equivalent
    """
    return (variable_in_m / density_of_water_in_gt_per_m3) * density_of_ice_in_gt_per_m3


def mwe2meter(variable_in_mwe: float, density_of_water_in_gt_per_m3: float = 997,
              density_of_ice_in_gt_per_m3: float = 850) -> float:
    """Function to convert a measurement of surface elevation change from meters water equivalent into meters.

    Parameters
    ----------
    variable_in_mwe : float
        The variable to be converted, with input units of mwe
    density_of_water_in_gt_per_m3 : float, optional
        The density of water in Gt per m3, by default 997
    density_of_ice_in_gt_per_m3 : float, optional
        The density of ice in Gt per m3, by default 850

    Returns
    -------
    Input variable converted into meters
    """
    return (variable_in_mwe * density_of_water_in_gt_per_m3) / density_of_ice_in_gt_per_m3


def gigatonne2slr(variable_in_gt: float, ocean_area: float = 3.625e8) -> float:
    """Function to convert a measurement of ice mass loss in gigatonnes into sea level rise (millimeters).

    Parameters
    ----------
    variable_in_gt : float
        The variable to be converted, with input units of gigatonnes
    ocean_area : float, optional
        The assumed area of the ocean in km2, by default 3.625e8

    Returns
    ----------
    Input variable converted into sea level rise (millimeters)
    """
    return abs(variable_in_gt / ocean_area) * 1e6
