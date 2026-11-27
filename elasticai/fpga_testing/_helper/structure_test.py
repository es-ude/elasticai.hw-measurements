from pathlib import Path
from shutil import rmtree

import pytest

import elasticai.fpga_testing as fpga_testing
from elasticai.fpga_testing import get_path_to_project

from .structure import copy_oss_cad_scripts, init_project_folder, set_makefile_target


@pytest.fixture(scope="module", autouse=True)
def path():
    path_dst = get_path_to_project(new_folder="temp_main")
    if path_dst.exists():
        rmtree(path_dst)

    yield path_dst


def test_init_project_folder(path: Path) -> None:
    checks = ["runs", "config", "scripts", "designs"]

    init_project_folder(new_folder="temp_main")
    assert path.exists()
    for folder in checks:
        assert (path / folder).exists()


def test_copy_scripts_init(path: Path) -> None:
    check_scripts = [
        "config.mk",
        "config_verilog_ccgm1a1.mk",
        "config_verilog_amd.mk",
        "config_verilog_up5k.mk",
    ]
    check_scripts.sort()
    check_main = ["Makefile", "fpga.nix", "devenv.nix", "devenv.yaml"]
    check_main.sort()

    init_project_folder(new_folder="temp_main")
    copy_oss_cad_scripts(dst=path)

    files_scripts = [file.name for file in (path / "scripts").glob("*.mk")]
    files_scripts.sort()
    assert files_scripts == check_scripts

    files_main = [file.name for file in path.glob("*") if file.is_file()]
    files_main.sort()
    assert files_main == check_main


def test_copy_scripts_reinit(path: Path) -> None:
    check_scripts = [
        "config.mk",
        "config_verilog_ccgm1a1.mk",
        "config_verilog_amd.mk",
        "config_verilog_up5k.mk",
    ]
    check_scripts.sort()
    check_main = ["Makefile", "fpga.nix", "devenv.nix", "devenv.yaml"]
    check_main.sort()

    init_project_folder(new_folder="temp_main")
    copy_oss_cad_scripts(dst=path)
    files_timestamp_init = dict()
    for file in path.rglob("*"):
        if file.is_file():
            files_timestamp_init.update({file.name: file.stat().st_mtime})

    copy_oss_cad_scripts(dst=path)
    files_timestamp_reinit = dict()
    for file in path.rglob("*"):
        if file.is_file():
            files_timestamp_reinit.update({file.name: file.stat().st_mtime})

    files_scripts = [file.name for file in (path / "scripts").glob("*.mk")]
    files_scripts.sort()
    assert files_scripts == check_scripts

    files_main = [file.name for file in path.glob("*") if file.is_file()]
    files_main.sort()
    assert files_main == check_main

    for key in files_timestamp_init.keys():
        if key in ["Makefile", "fpga.nix", "devenv.nix", "devenv.yaml"]:
            assert files_timestamp_init[key] == files_timestamp_reinit[key]
        else:
            assert files_timestamp_init[key] < files_timestamp_reinit[key]


def test_copy_scripts_keeps_existing_main_files(path: Path) -> None:
    init_project_folder(new_folder="temp_main")
    copy_oss_cad_scripts(dst=path)
    (path / "Makefile").write_text("DEVICE = CCGM1A1\n")
    (path / "fpga.nix").write_text("{ }\n")

    copy_oss_cad_scripts(dst=path)

    assert (path / "Makefile").read_text() == "DEVICE = CCGM1A1\n"
    assert (path / "fpga.nix").read_text() == "{ }\n"


def test_copy_scripts_copies_missing_main_files(path: Path) -> None:
    path_template = Path(fpga_testing.__file__).parent / "template" / "oss_cad"
    init_project_folder(new_folder="temp_main")
    copy_oss_cad_scripts(dst=path)
    (path / "Makefile").unlink()
    (path / "fpga.nix").unlink()

    copy_oss_cad_scripts(dst=path)

    for file_name in ["Makefile", "fpga.nix"]:
        assert (path / file_name).read_bytes() == (path_template / file_name).read_bytes()


def _get_active_settings(path2makefile: Path) -> list[str]:
    return [
        line
        for line in path2makefile.read_text().splitlines()
        if line.startswith("DEVICE") or line.startswith("PACKAGE")
    ]


@pytest.mark.parametrize(
    "device, package",
    [
        ("UP5K", "sg48"),
        ("CCGM1A1", None),
        ("AMD", "xc7s50ftgb196-1"),
        ("AMD", "xc7a100tcsg324-1"),
    ],
)
def test_set_makefile_target_selects_block(tmp_path: Path, device: str, package: str | None) -> None:
    path2makefile = tmp_path / "Makefile"
    path_template = Path(fpga_testing.__file__).parent / "template" / "oss_cad" / "Makefile"
    path2makefile.write_text(path_template.read_text())

    set_makefile_target(path2makefile, device=device, package=package)

    expected = [f"DEVICE = {device}"] + ([f"PACKAGE = {package}"] if package else [])
    assert _get_active_settings(path2makefile) == expected
    assert "TOP = TOP_MODULE" in path2makefile.read_text()
    assert "include scripts/config.mk" in path2makefile.read_text()


def test_set_makefile_target_is_idempotent(tmp_path: Path) -> None:
    path2makefile = tmp_path / "Makefile"
    path_template = Path(fpga_testing.__file__).parent / "template" / "oss_cad" / "Makefile"
    path2makefile.write_text(path_template.read_text())

    set_makefile_target(path2makefile, device="AMD", package="xc7a100tcsg324-1")
    first = path2makefile.read_text()
    set_makefile_target(path2makefile, device="AMD", package="xc7a100tcsg324-1")

    assert path2makefile.read_text() == first


def test_set_makefile_target_adds_block_for_unknown_target(tmp_path: Path) -> None:
    path2makefile = tmp_path / "Makefile"
    path2makefile.write_text("DEVICE = UP5K\nPACKAGE = sg48\nTOP = TOP_MODULE\n")

    set_makefile_target(path2makefile, device="AMD", package="xc7s15ftgb196-1")
    set_makefile_target(path2makefile, device="AMD", package="xc7s15ftgb196-1")

    assert _get_active_settings(path2makefile) == ["DEVICE = AMD", "PACKAGE = xc7s15ftgb196-1"]
    assert path2makefile.read_text().count("#DEVICE = UP5K") == 1
    assert "TOP = TOP_MODULE" in path2makefile.read_text()
