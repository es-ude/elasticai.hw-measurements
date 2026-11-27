import argparse
from collections.abc import Callable
from pathlib import Path

from elasticai.fpga_testing import copy_oss_cad_scripts
from elasticai.fpga_testing.copy_design import (
    copy_design_arty7_files,
    copy_design_env5_files,
    copy_design_env6mini_files,
)

BOARDS: dict[str, Callable[..., None]] = {
    "arty7": copy_design_arty7_files,
    "env5": copy_design_env5_files,
    "env6_mini": copy_design_env6mini_files,
}


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Prepares a project folder to build the bitstream of a board"
    )
    parser.add_argument("board", choices=sorted(BOARDS))
    parser.add_argument("dest", type=Path)
    args = parser.parse_args()

    project = args.dest.resolve()
    for folder in ("scripts", "designs"):
        (project / folder).mkdir(parents=True, exist_ok=True)
    copy_oss_cad_scripts(dst=project)
    BOARDS[args.board](dest=project / "designs")


if __name__ == "__main__":
    main()
