import pytest

from elasticai.fpga_testing.copy_design import copy_design_env6mini_files
from elasticai.fpga_testing.tests import run_copied_test


@pytest.mark.simulation
def test_echo() -> None:
    run_copied_test(copy_design_env6mini_files, "env6_mini", "test_echo")


@pytest.mark.simulation
def test_led() -> None:
    run_copied_test(copy_design_env6mini_files, "env6_mini", "test_led")
