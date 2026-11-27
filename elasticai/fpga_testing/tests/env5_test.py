import pytest

from elasticai.fpga_testing.copy_design import copy_design_env5_files
from elasticai.fpga_testing.tests import run_copied_test


@pytest.mark.simulation
def test_echo() -> None:
    run_copied_test(copy_design_env5_files, "env5", "test_echo")


@pytest.mark.simulation
def test_led() -> None:
    run_copied_test(copy_design_env5_files, "env5", "test_led")
