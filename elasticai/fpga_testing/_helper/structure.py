import re
from os import remove
from pathlib import Path
from shutil import copyfile

import elasticai.fpga_testing as dut
from elasticai.fpga_testing import get_path_to_project


def init_project_folder(new_folder: str = "") -> None:
    """Generating folder structure in first run
    :param new_folder:      Name of the new folder to create (test case)
    :return:                None
    """

    folder_structure = ["runs", "config", "scripts", "designs"]

    path2start = get_path_to_project(new_folder)
    for folder_name in folder_structure:
        fold = path2start / folder_name
        fold.mkdir(parents=True, exist_ok=True)


def copy_oss_cad_scripts(dst: Path = get_path_to_project()) -> None:
    """Copies oss cad scripts and devenv scripts to destination folder.
    The scripts (*.mk) are updated every time, the main files (Makefile, fpga.nix, devenv.nix, devenv.yaml) are only copied if
    they do not exist, so the settings of the project (e.g. device, top module, frequency) are kept
    :param dst: Path to the destination folder
    :return:    None"""
    path_to_template = Path(dut.__file__).parent / "template" / "oss_cad"

    dst.mkdir(parents=True, exist_ok=True)
    # --- Step #1: Copying script files
    for file in path_to_template.glob("*.mk"):
        path2file = dst.absolute() / "scripts" / file.name
        if path2file.exists():
            remove(path2file.as_posix())
        copyfile(src=file.absolute(), dst=path2file)

    # --- Step #2: Copying main files (only if they are not available)
    files_main = ["Makefile", "fpga.nix", "devenv.nix", "devenv.yaml"]
    for file_name in files_main:
        path2file = dst.absolute() / file_name
        if not path2file.exists():
            copyfile(src=(path_to_template / path2file.name).as_posix(), dst=path2file.as_posix())


_PATTERN_SETTING = re.compile(r"^#?\s*(DEVICE|PACKAGE)\s*=\s*(\S*)")
_PATTERN_HEADER = "# --- Settings for"


def _get_name_of_setting(line: str) -> str | None:
    match = _PATTERN_SETTING.match(line)
    return match.group(1) if match else None


def set_makefile_target(path2makefile: Path, device: str, package: str | None = None) -> None:
    """Selects the target device in the Makefile: the settings block of the device is activated (uncommented),
    the DEVICE/PACKAGE lines of all other blocks are commented out. If the Makefile has no block for the device,
    a new block is inserted. All other lines of the Makefile (e.g. TOP, FREQ) stay untouched
    :param path2makefile:   Path to the Makefile
    :param device:          Value of DEVICE (e.g. UP5K, AMD, CCGM1A1)
    :param package:         Value of PACKAGE (e.g. sg48), None if the device has no package
    :return:                None
    """
    lines = path2makefile.read_text().splitlines()
    idx_settings = [idx for idx, line in enumerate(lines) if _PATTERN_SETTING.match(line)]

    blocks: list[list[int]] = []
    for idx, line in enumerate(lines):
        if line.startswith(_PATTERN_HEADER):
            block = []
            for idx_next in range(idx + 1, len(lines)):
                if not _PATTERN_SETTING.match(lines[idx_next]):
                    break
                block.append(idx_next)
            part: list[int] = []
            for idx_block in block:
                if _get_name_of_setting(lines[idx_block]) == "DEVICE" and part:
                    blocks.append(part)
                    part = []
                part.append(idx_block)
            if part:
                blocks.append(part)

    idx_active: set[int] = set()
    for block in blocks:
        values = {
            m.group(1): m.group(2) for m in (_PATTERN_SETTING.match(lines[idx]) for idx in block) if m
        }
        if values.get("DEVICE") == device and values.get("PACKAGE") == package:
            idx_active = set(block)
            break

    lines_new = []
    for idx, line in enumerate(lines):
        if idx in idx_settings:
            setting = line.lstrip("#").strip()
            lines_new.append(setting if idx in idx_active else f"#{setting}")
        else:
            lines_new.append(line)

    if not idx_active:
        block_new = [f"{_PATTERN_HEADER} {device}", f"DEVICE = {device}"]
        if package is not None:
            block_new.append(f"PACKAGE = {package}")
        if blocks:
            position = blocks[0][0] - 1
        elif idx_settings:
            position = idx_settings[0]
        else:
            position = 0
        lines_new[position:position] = block_new

    path2makefile.write_text("\n".join(lines_new) + "\n")
