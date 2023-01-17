"""
Density uncertainty in relation to the length of the survey period.
"""


def get_density_uncertainty_over_survey_period(time_period_in_fractional_years) -> int:
    """
    Lazy implementation of a density uncertainty catalogue at different time resolutions,
    approximately following Huss (2013, Fig. 4d).
    See the GlaMBIE Assessment Algorithm document for more information,

    Parameters
    ----------
    time_period_in_fractional_years : float
        time period of desired density uncertainty

    Returns
    -------
    int
        Density uncertainty in kg/m^3
    """
    if time_period_in_fractional_years < 1:
        return 480
    if time_period_in_fractional_years >= 1 and time_period_in_fractional_years < 5:
        return 240
    if time_period_in_fractional_years >= 5 and time_period_in_fractional_years < 10:
        return 120
    if time_period_in_fractional_years >= 10:
        return 60
