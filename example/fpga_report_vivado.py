from elasticai.fpga_testing.reports import copy_vivado_implementation_results
from elasticai.fpga_testing import get_path_to_project
from pathlib import Path


if __name__ == '__main__':
    path_main = get_path_to_project()

    copy_vivado_implementation_results(
        path2project=Path("/Volumes/USB/test_env5"),
        path2save=path_main / "temp_new"
    )
