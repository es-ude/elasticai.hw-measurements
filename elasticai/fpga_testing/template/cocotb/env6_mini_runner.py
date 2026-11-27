import sys
from pathlib import Path

import pytest
from elasticai.creator.testing.cocotb_runner import run_cocotb_sim_for_src_dir

PATH_TESTS = Path(__file__).parent
PATH_DESIGNS = PATH_TESTS.parent / "designs"
PARAMS = {
    "TEST_ENV_CMDS_BITWIDTH": 2,
    "TEST_ENV_ADR_WIDTH": 6,
    "TEST_ENV_DATA_BITWIDTH": 16,
}


def _run_bench(bench: str) -> None:
    sys.path.insert(0, PATH_TESTS.as_posix())
    run_cocotb_sim_for_src_dir(
        src_files=sorted(PATH_DESIGNS.rglob("*.v")),
        top_module_name="TOP_MODULE",
        cocotb_test_module=bench,
        defines={"SIMULATION": 1},
        params=PARAMS,
    )


@pytest.mark.simulation
def test_echo() -> None:
    _run_bench("spi_echo_bench")


@pytest.mark.simulation
def test_led() -> None:
    _run_bench("spi_led_bench")
