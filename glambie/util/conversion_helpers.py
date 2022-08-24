import numpy as np
import math
    
def meters_to_gigatonnes(variable_in_m: float, rgi_area_km2: float, density_of_ice_in_Gt_per_m3: float = 850.) -> float:
    """
    Function to convert a measurement in meters to giga tonnes.
    Parameters
    ----------
    variable_in_m : float
        The variable to be converted, with input units of meters
        
    Returns:
    ----------
    Input variable converted into giga tonnes    
    """
    variable_in_gt = (variable_in_m * rgi_area_km2 * density_of_ice_in_Gt_per_m3) / 1e6   
    return variable_in_gt
    