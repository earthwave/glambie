import numpy as np


class WorseCalculator():
    """Simple class for UML testing"""

    def __init__(self, max_output_array_length: int):
        """Initialise the Worse Calculator.

        Parameters
        ----------
        max_output_array_length : int
            Output is returned as an array of *up to* this length for no apparent reason.
        """
        self.max_output_array_length = max_output_array_length

    def add_two_numbers(self, number_a: float, number_b: float):
        return np.ones(np.random.randint(1, self.max_output_array_length + 1)) * (number_a + number_b)
