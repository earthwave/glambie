import pytest

from glambie.example_module_a import BadCalculator


@pytest.fixture()
def example_bad_calculator():
    return BadCalculator(output_array_length=4)


def test_bad_calculator_can_be_instantiated(example_bad_calculator):
    assert example_bad_calculator is not None


def test_bad_calculator_output_length_obeyed(example_bad_calculator):
    assert len(example_bad_calculator.add_two_numbers(1, 2)) == 4


def test_bad_calculator_output_correct(example_bad_calculator):
    assert all(example_bad_calculator.add_two_numbers(2, 6) == 8)
