import numpy as np


class BadCalculator():
    """Simple class for UML testing"""

    def __init__(self, output_array_length: int):
        """Initialise the Bad Calculator.

        Parameters
        ----------
        output_array_length : int
            Output is returned as an array of this length for no apparent reason.
        """
        self.output_array_length = output_array_length

    def add_two_numbers(self, number_a: float, number_b: float):
        return np.ones(self.output_array_length) * (number_a + number_b)
