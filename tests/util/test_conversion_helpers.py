from glambie.util.conversion_helpers import meters_to_gigatonnes

def test_meters_to_gigatonnes():
    test_variable_in_m = 20
    test_rgi_area_km2 = 1000
    assert meters_to_gigatonnes(test_variable_in_m, test_rgi_area_km2) == 17
    #if non-default ice density is used
    test_density_of_ice_in_Gt_per_m3 = 800
    assert meters_to_gigatonnes(test_variable_in_m, test_rgi_area_km2, test_density_of_ice_in_Gt_per_m3) == 16