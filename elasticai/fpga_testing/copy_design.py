from enum import Enum
from pathlib import Path
from shutil import copyfile, copytree

import elasticai.fpga_testing as dut
from elasticai.fpga_testing import get_path_to_project
from elasticai.fpga_testing._helper.structure import set_makefile_target


def _get_template_path() -> Path:
    return Path(dut.__file__).parent / "template"


def _get_basic_path() -> Path:
    return get_path_to_project() / "designs"


def _copy_cocotb_files(board: str, interface: str, dest_tests: Path) -> None:
    path2cocotb = _get_template_path() / "cocotb"
    dest_tests.mkdir(parents=True, exist_ok=True)
    files = ["cocotb_funcs.py", f"{interface}_echo_bench.py", f"{interface}_led_bench.py"]
    for file in files:
        copyfile(src=path2cocotb / file, dst=dest_tests / file)
    copyfile(src=path2cocotb / f"{board}_runner.py", dst=dest_tests / f"{board}_test.py")


def _select_target_in_makefile(
    makefile: Path | None, dest: Path, device: str, package: str | None
) -> None:
    path2makefile = makefile if makefile is not None else dest.parent / "Makefile"
    if path2makefile.is_file():
        set_makefile_target(path2makefile, device=device, package=package)


def _copy_design_files(src_device: Path, src_common: Path, dest: Path) -> None:
    dest.mkdir(parents=True, exist_ok=True)
    if not src_common == Path("."):
        copytree(src=src_common, dst=dest, dirs_exist_ok=True)
    if not src_device == Path("."):
        copytree(src=src_device, dst=dest, dirs_exist_ok=True)


def copy_design_arty7_files(
    dest: Path = _get_basic_path(), dest_tests: Path | None = None, makefile: Path | None = None
) -> None:
    """Function for copying the design files and the cocotb tests to test structures on FPGA (here: DevBoard Digilent Arty A7)
    :param dest:        Path with destination folder to copy all design files into
    :param dest_tests:  Path with destination folder to copy the cocotb tests (testbenches, runner `arty7_test.py` and `cocotb_funcs.py`) into
                        [Default: folder `tests` next to the destination folder of the design files]
    :param makefile:    Path to the Makefile, in which DEVICE and PACKAGE of the board are selected
                        [Default: file `Makefile` next to the destination folder of the design files, skipped if it does not exist]
    :return:            None
    """
    path2device = _get_template_path() / "arty7"
    path2common = _get_template_path() / "common"
    _copy_design_files(
        src_device=path2device,
        src_common=path2common,
        dest=dest,
    )
    _copy_cocotb_files(
        board="arty7",
        interface="uart",
        dest_tests=dest_tests if dest_tests is not None else dest.parent / "tests",
    )
    _select_target_in_makefile(makefile=makefile, dest=dest, device="AMD", package="xc7a100tcsg324-1")


def copy_design_env5_files(
    dest: Path = _get_basic_path(), dest_tests: Path | None = None, makefile: Path | None = None
) -> None:
    """Function for copying the design files and the cocotb tests to test structures on FPGA (here: elasticAI.env5)
    :param dest:        Path with destination folder to copy all design files into
    :param dest_tests:  Path with destination folder to copy the cocotb tests (testbenches, runner `env5_test.py` and `cocotb_funcs.py`) into
                        [Default: folder `tests` next to the destination folder of the design files]
    :param makefile:    Path to the Makefile, in which DEVICE and PACKAGE of the board are selected
                        [Default: file `Makefile` next to the destination folder of the design files, skipped if it does not exist]
    :return:            None
    """
    path2device = _get_template_path() / "env5"
    path2common = _get_template_path() / "common"
    _copy_design_files(
        src_device=path2device,
        src_common=path2common,
        dest=dest,
    )
    _copy_cocotb_files(
        board="env5",
        interface="spi",
        dest_tests=dest_tests if dest_tests is not None else dest.parent / "tests",
    )
    _select_target_in_makefile(makefile=makefile, dest=dest, device="AMD", package="xc7s50ftgb196-1")


def copy_design_env6mini_files(
    dest: Path = _get_basic_path(), dest_tests: Path | None = None, makefile: Path | None = None
) -> None:
    """Function for copying the design files and the cocotb tests to test structures on FPGA (here: elasticAI.env6-mini)
    :param dest:        Path with destination folder to copy all design files into
    :param dest_tests:  Path with destination folder to copy the cocotb tests (testbenches, runner `env6_mini_test.py` and `cocotb_funcs.py`) into
                        [Default: folder `tests` next to the destination folder of the design files]
    :param makefile:    Path to the Makefile, in which DEVICE and PACKAGE of the board are selected
                        [Default: file `Makefile` next to the destination folder of the design files, skipped if it does not exist]
    :return:            None
    """
    path2device = _get_template_path() / "env6_mini"
    path2common = _get_template_path() / "common"
    _copy_design_files(
        src_device=path2device,
        src_common=path2common,
        dest=dest,
    )
    _copy_cocotb_files(
        board="env6_mini",
        interface="spi",
        dest_tests=dest_tests if dest_tests is not None else dest.parent / "tests",
    )
    _select_target_in_makefile(makefile=makefile, dest=dest, device="UP5K", package="sg48")


class TargetsSkeleton(Enum):
    DNN = "dnn"
    FILTER = "filter"
    ROM = "rom"
    RAM = "ram"
    MATH_MULT = "math_mult"
    MATH_MAC = "math_mac"


def copy_skeleton(name: TargetsSkeleton, num_id: int, dest: Path) -> None:
    """Function for copying a skeleton to test structures on FPGAs
    :param name:    Name of skeleton file [dnn, filter, math, ram, rom]
    :param num_id:  ID number of skeleton
    :param dest:    Path with destination folder to copy all files into
    :return:        None
    """
    if name.value.lower() not in [t.value for t in TargetsSkeleton]:
        raise ValueError(f"{name.value} is not a valid skeleton name")

    path2design = _get_template_path() / "skeleton"
    dest.mkdir(parents=True, exist_ok=True)
    copyfile(
        src=path2design / f"skeleton_{name.value}.v".lower(),
        dst=dest / f"skeleton_{name.value}_{num_id}.v".lower(),
    )
