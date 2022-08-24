def meters_to_gigatonnes(variable_in_m: float, rgi_area_km2: float, density_of_ice_in_Gt_per_m3: float = 850) -> float:
    """
    Function to convert a measurement in meters to giga tonnes.

    Parameters
    ----------
    variable_in_m : float
        The variable to be converted, with input units of meters
    rgi_area_km2 : float
        The area of the region in km2
    density_of_ice_in_Gt_per_m3 : , optional
        The density of ice in Gt per m3, by default 850

    Returns:
    ----------
    Input variable converted into giga tonnes
    """
    variable_in_gt = variable_in_m * density_of_ice_in_Gt_per_m3 * (rgi_area_km2 / 1e6)
    return variable_in_gt


def meters_to_meters_water_equivalent(variable_in_m: float, density_of_water_in_Gt_per_m3: float = 997,
                                      density_of_ice_in_Gt_per_m3: float = 850) -> float:
    """
    Function to convert a measurement in meters to meters water equivalent. mwe will always be lower value than m,
    due to the difference in density of ice and water


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
    variable_in_mwe = (variable_in_m / density_of_water_in_Gt_per_m3) * density_of_ice_in_Gt_per_m3
    return variable_in_mwe
