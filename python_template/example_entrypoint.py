"""
The single comand line entrypoint for the package.
Note that not all packages need a command line entry point.
"""
import argparse

from glambie.example_module_a import BadCalculator
from glambie.example_sub_package.example_module_b import WorseCalculator


def main():
    # Build the argument parser
    parser = argparse.ArgumentParser(
        prog='glambie', description='Perform some bad calculations on two integers.')
    parser.add_argument('-a', dest='integer_a', type=int, help='The first integer')
    parser.add_argument('-b', dest='integer_b', type=int, help='The second integer')

    # parse the input arguments
    args = parser.parse_args()

    # instantiate some calculators
    bad_calculator = BadCalculator(output_array_length=5)
    worse_calculator = WorseCalculator(max_output_array_length=10)

    # use the calculators to perform some calculations
    print(f"Bad Calculator Output: {bad_calculator.add_two_numbers(args.integer_a, args.integer_b)}")
    print(f"Worse Calculator Output: {worse_calculator.add_two_numbers(args.integer_a, args.integer_b)}")
