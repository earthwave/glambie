import pytest

from glambie.example_sub_package.example_module_b import WorseCalculator


@pytest.fixture()
def example_worse_calculator():
    return WorseCalculator(max_output_array_length=5)


def test_worse_calculator_can_be_instantiated(example_worse_calculator):
    assert example_worse_calculator is not None


def test_worse_calculator_max_output_array_length_obeyed(example_worse_calculator):
    assert len(example_worse_calculator.add_two_numbers(1, 2)) <= 5


def test_worse_calculator_output_correct(example_worse_calculator):
    assert all(example_worse_calculator.add_two_numbers(1, 2) == 3)
