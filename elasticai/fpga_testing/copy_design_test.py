from shutil import copyfile, rmtree

import pytest

from elasticai.fpga_testing import get_path_to_project

from .copy_design import (
    TargetsSkeleton,
    _get_template_path,
    copy_design_arty7_files,
    copy_design_env5_files,
    copy_design_env6mini_files,
    copy_skeleton,
)


@pytest.fixture(scope="module", autouse=True)
def path():
    path2temp = get_path_to_project() / "temp_build"
    if path2temp.exists():
        rmtree(path2temp)
    path2temp.mkdir(parents=True, exist_ok=True)
    yield path2temp


def test_template_path() -> None:
    dst = _get_template_path()
    chck = get_path_to_project() / "elasticai" / "fpga_testing" / "template"
    assert dst.as_posix() == chck.as_posix()


def test_copy_design_arty7_files(path) -> None:
    path2dst = path / "arty7"
    copy_design_arty7_files(dest=path2dst)

    files_available = [file.name for file in path2dst.rglob("*.*")]
    files_available.sort()
    files_check = [
        "io.xdc",
        "test_dut.v",
        "top_module.v",
        "uart_com.v",
        "uart_fifo.v",
        "uart_middleware.v",
        "skeleton_echo.v",
    ]
    files_check.sort()

    assert files_available == files_check


def test_copy_design_env5_files(path) -> None:
    path2dst = path / "env5"
    copy_design_env5_files(dest=path2dst)

    files_available = [file.name for file in path2dst.rglob("*.*")]
    files_available.sort()
    files_check = [
        "io.xdc",
        "test_dut.v",
        "top_module.v",
        "spi_middleware.v",
        "spi_slave_wclk.v",
        "skeleton_echo.v",
    ]
    files_check.sort()

    assert files_available == files_check


def test_copy_design_arty7_files_copies_the_cocotb_tests(path) -> None:
    path2dst = path / "arty7_cocotb"
    copy_design_arty7_files(dest=path2dst / "designs")

    files_available = sorted(file.name for file in (path2dst / "tests").iterdir())
    assert files_available == [
        "arty7_test.py",
        "cocotb_funcs.py",
        "uart_echo_bench.py",
        "uart_led_bench.py",
    ]


def test_copy_design_env5_files_copies_the_cocotb_tests(path) -> None:
    path2dst = path / "env5_cocotb"
    copy_design_env5_files(dest=path2dst / "designs")

    files_available = sorted(file.name for file in (path2dst / "tests").iterdir())
    assert files_available == [
        "cocotb_funcs.py",
        "env5_test.py",
        "spi_echo_bench.py",
        "spi_led_bench.py",
    ]


def test_copy_design_env6mini_files_copies_the_cocotb_tests(path) -> None:
    path2dst = path / "env6_mini_cocotb"
    copy_design_env6mini_files(dest=path2dst / "designs")

    files_available = sorted(file.name for file in (path2dst / "tests").iterdir())
    assert files_available == [
        "cocotb_funcs.py",
        "env6_mini_test.py",
        "spi_echo_bench.py",
        "spi_led_bench.py",
    ]


def test_copy_design_files_copies_the_cocotb_tests_into_given_folder(path) -> None:
    path2dst = path / "env5_own_tests"
    path2tests = path / "env5_own_tests_folder"
    copy_design_env5_files(dest=path2dst / "designs", dest_tests=path2tests)

    assert (path2tests / "env5_test.py").is_file()
    assert not (path2dst / "tests").exists()


@pytest.mark.parametrize(
    "copy_design, device, package",
    [
        (copy_design_arty7_files, "AMD", "xc7a100tcsg324-1"),
        (copy_design_env5_files, "AMD", "xc7s50ftgb196-1"),
        (copy_design_env6mini_files, "UP5K", "sg48"),
    ],
)
def test_copy_design_files_selects_target_in_makefile(
    path, copy_design, device: str, package: str
) -> None:
    path2project = path / f"makefile_{device}_{package}"
    path2project.mkdir(parents=True)
    copyfile(_get_template_path() / "oss_cad" / "Makefile", path2project / "Makefile")

    copy_design(dest=path2project / "designs")

    settings = [
        line
        for line in (path2project / "Makefile").read_text().splitlines()
        if line.startswith("DEVICE") or line.startswith("PACKAGE")
    ]
    assert settings == [f"DEVICE = {device}", f"PACKAGE = {package}"]


def test_copy_design_files_selects_target_in_given_makefile(path) -> None:
    path2dst = path / "env6_own_makefile"
    path2makefile = path / "env6_own_makefile_file" / "Makefile"
    path2makefile.parent.mkdir(parents=True)
    copyfile(_get_template_path() / "oss_cad" / "Makefile", path2makefile)
    path2makefile.write_text(path2makefile.read_text().replace("DEVICE = UP5K", "#DEVICE = UP5K"))

    copy_design_env6mini_files(dest=path2dst / "designs", makefile=path2makefile)

    assert "\nDEVICE = UP5K\n" in path2makefile.read_text()
    assert not (path2dst / "Makefile").exists()


def test_cocotb_benches_use_the_functions_of_cocotb_funcs() -> None:
    path2cocotb = _get_template_path() / "cocotb"
    benches = sorted(path2cocotb.glob("*_bench.py"))

    assert len(benches) == 4
    for bench in benches:
        assert "from cocotb_funcs import" in bench.read_text()


def test_copy_design_env6mini_files(path) -> None:
    path2dst = path / "env6mini"
    copy_design_env6mini_files(dest=path2dst)

    files_available = [file.name for file in path2dst.rglob("*.*")]
    files_available.sort()
    files_check = [
        "io.pcf",
        "test_dut.v",
        "top_module.v",
        "spi_middleware.v",
        "spi_slave_wclk.v",
        "skeleton_echo.v",
    ]
    files_check.sort()

    assert files_available == files_check


def test_copy_skeleton_string_input(path) -> None:
    path2dst = path / "skeletons"
    with pytest.raises(AttributeError):
        copy_skeleton(name="wrong", num_id=0, dest=path2dst)


def test_copy_skeleton_not_available(path) -> None:
    path2dst = path / "skeletons"
    with pytest.raises(AttributeError):
        copy_skeleton(name=TargetsSkeleton.END, num_id=0, dest=path2dst)


def test_copy_skeleton_dnn(path) -> None:
    used_modules = [
        TargetsSkeleton.DNN,
        TargetsSkeleton.FILTER,
        TargetsSkeleton.MATH_MULT,
        TargetsSkeleton.MATH_MAC,
        TargetsSkeleton.RAM,
        TargetsSkeleton.ROM,
    ]

    for idx, module in enumerate(used_modules):
        path2dst = path / "skeletons" / module.value.lower()
        copy_skeleton(name=module, num_id=idx, dest=path2dst)

        files_available = [file.name for file in path2dst.rglob("*.*")]
        files_available.sort()
        files_check = [f"skeleton_{module.value.lower()}_{idx}.v"]
        files_check.sort()
        assert files_available == files_check
