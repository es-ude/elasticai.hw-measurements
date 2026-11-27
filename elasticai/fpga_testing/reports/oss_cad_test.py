from pathlib import Path
from shutil import rmtree

import pytest

from elasticai.fpga_testing import get_path_to_project

from .oss_cad import (
    NextpnrMetrics,
    NextpnrTimingSummary,
    NextpnrUtilizationEntry,
    NextpnrUtilizationSummary,
    copy_osscad_implementation_results,
)

TIMING_REPORT = """Total number of logic levels: 3
Total path delay: 17.00 ns (58.82 MHz)
"""

UTILIZATION_ENTRIES = {
    "ICESTORM_LC": (162, 5280),
    "ICESTORM_RAM": (0, 30),
    "SB_IO": (8, 96),
    "SB_GB": (4, 8),
    "ICESTORM_PLL": (0, 1),
    "SB_WARMBOOT": (0, 1),
    "ICESTORM_DSP": (0, 8),
    "ICESTORM_HFOSC": (0, 1),
    "ICESTORM_LFOSC": (0, 1),
    "SB_I2C": (0, 2),
    "SB_SPI": (0, 2),
    "IO_I3C": (0, 2),
    "SB_LEDDA_IP": (0, 1),
    "SB_RGBA_DRV": (0, 1),
    "ICESTORM_SPRAM": (0, 4),
}


def _utilization_report() -> str:
    lines = ["Info: Device utilisation:"]
    for name, (used, available) in UTILIZATION_ENTRIES.items():
        lines.append(f"Info: \t{name:>16}: {used:>5}/{available:>5} {int(100 * used / available):>3}%")
    return "\n".join(lines) + "\n\nInfo: Placed 8 cells based on constraints.\n"


@pytest.fixture(autouse=True)
def osscad_path(tmp_path: Path):
    path = tmp_path / "env6_mini"
    path.mkdir()
    (path / "TOP_MODULE.bin").write_bytes(bytes(range(64)))
    (path / "TOP_MODULE_timing.rpt").write_text(TIMING_REPORT)
    (path / "TOP_MODULE_util_impl.rpt").write_text(_utilization_report())
    (path / "TOP_MODULE_util_sync.rpt").write_text("=== TOP_MODULE ===\n")
    yield path


@pytest.fixture(autouse=True)
def temp_path():
    path = get_path_to_project("temp_reports") / "osscad"
    if path.exists():
        rmtree(path)
    yield path


def test_copy_reports(osscad_path: Path, temp_path: Path) -> None:
    copy_osscad_implementation_results(
        path2project=osscad_path,
        path2save=temp_path,
    )
    assert temp_path.exists()
    assert temp_path.is_dir()

    files_temp = [file.name for file in temp_path.iterdir()]
    files_temp.sort()
    files_proj = [file.name for file in osscad_path.iterdir()]
    files_proj.sort()
    assert files_temp == files_proj


def test_extract_timing(osscad_path: Path) -> None:
    summary = NextpnrTimingSummary.from_rpt(osscad_path)
    assert type(summary) == NextpnrTimingSummary
    assert summary.logic_levels == 3
    assert summary.max_frequency_mhz == 58.82
    assert summary.total_path_delay_ns == 17.0


def test_extract_utilization(osscad_path: Path) -> None:
    summary = NextpnrUtilizationSummary.from_rpt(osscad_path)
    assert type(summary) == NextpnrUtilizationSummary
    assert len(summary.entries) == 15
    assert type(summary.entries["ICESTORM_LC"]) == NextpnrUtilizationEntry
    assert summary.entries["ICESTORM_LC"].used == 162


def test_extract_metrics(osscad_path: Path) -> None:
    summary = NextpnrMetrics.from_rpt(osscad_path)
    assert type(summary) == NextpnrMetrics
    assert type(summary.timing) == NextpnrTimingSummary
    assert type(summary.utilization) == NextpnrUtilizationSummary
    assert summary.timing.max_frequency_mhz == 58.82
