from collections.abc import Callable
from importlib.util import module_from_spec, spec_from_file_location
from shutil import rmtree

from elasticai.fpga_testing import get_path_to_project


def run_copied_test(copy_design: Callable[..., None], board: str, test_name: str) -> None:
    """Copying the design and the cocotb tests of a board into a new folder and running one test of the copied runner
    :param copy_design: Function for copying the design (and tests) of the board
    :param board:       Name of the board (name of the copied runner is `<board>_test.py`)
    :param test_name:   Name of the test function in the copied runner
    :return:            None
    """
    path_project = get_path_to_project() / "temp_build" / f"{board}_{test_name}"
    if path_project.exists():
        rmtree(path_project)
    copy_design(dest=path_project / "designs")

    path_runner = path_project / "tests" / f"{board}_test.py"
    spec = spec_from_file_location(f"copied_test_{board}", path_runner)
    assert spec is not None and spec.loader is not None
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    getattr(module, test_name)()
