from pathlib import Path
from shutil import rmtree

import pytest

from elasticai.hw_measurements import get_path_to_project

from .vivado import (
    VivadoMetrics,
    VivadoPowerReport,
    VivadoTimingSummary,
    VivadoUtilizationSummary,
    copy_vivado_implementation_results,
)

HEADER = """---------------------------------------------------------------------------------------------------------------------------------------------
| Tool Version : Vivado v.2024.2 (lin64) Build 5239630 Fri Nov 08 22:34:34 MST 2024
| Design       : TOP_MODULE
| Device       : {device}
| Design State : Routed
---------------------------------------------------------------------------------------------------------------------------------------------
"""

TIMING_REPORT = (
    HEADER.format(device="7a35ti-csg324")
    + """
Timing Summary Report

------------------------------------------------------------------------------------------------
| Design Timing Summary
| ---------------------
------------------------------------------------------------------------------------------------

    WNS(ns)      TNS(ns)  TNS Failing Endpoints  TNS Total Endpoints      WHS(ns)      THS(ns)  THS Failing Endpoints  THS Total Endpoints     WPWS(ns)     TPWS(ns)  TPWS Failing Endpoints  TPWS Total Endpoints
    -------      -------  ---------------------  -------------------      -------      -------  ---------------------  -------------------     --------     --------  ----------------------  --------------------
      0.759        0.000                      0                 1550        0.117        0.000                      0                 1550        4.500        0.000                       0                  1190

All user specified timing constraints are met.

------------------------------------------------------------------------------------------------
"""
)

UTILIZATION_REPORT = (
    HEADER.format(device="xc7a35ticsg324-1L")
    + """
1. Slice Logic
--------------

+----------------------------+------+-------+------------+-----------+-------+
|          Site Type         | Used | Fixed | Prohibited | Available | Util% |
+----------------------------+------+-------+------------+-----------+-------+
| Slice LUTs                 |  636 |     0 |          0 |     20800 |  3.06 |
| Slice Registers            | 1186 |     0 |          0 |     41600 |  2.85 |
| F7 Muxes                   |    2 |     0 |          0 |     16300 |  0.01 |
| F8 Muxes                   |    1 |     0 |          0 |      8150 |  0.01 |
+----------------------------+------+-------+------------+-----------+-------+


3. Memory
---------

+-------------------+------+-------+------------+-----------+-------+
|     Site Type     | Used | Fixed | Prohibited | Available | Util% |
+-------------------+------+-------+------------+-----------+-------+
| Block RAM Tile    |    0 |     0 |          0 |        50 |  0.00 |
+-------------------+------+-------+------------+-----------+-------+


4. DSP
------

+----------------+------+-------+------------+-----------+-------+
|    Site Type   | Used | Fixed | Prohibited | Available | Util% |
+----------------+------+-------+------------+-----------+-------+
| DSPs           |    0 |     0 |          0 |        90 |  0.00 |
+----------------+------+-------+------------+-----------+-------+


5. IO and GT Specific
---------------------

+-----------------------------+------+-------+------------+-----------+-------+
|          Site Type          | Used | Fixed | Prohibited | Available | Util% |
+-----------------------------+------+-------+------------+-----------+-------+
| Bonded IOB                  |    7 |     7 |          0 |       210 |  3.33 |
+-----------------------------+------+-------+------------+-----------+-------+
"""
)

POWER_REPORT = (
    HEADER.format(device="xc7a35ticsg324-1L")
    + """
1. Summary
----------

+--------------------------+--------------+
| Total On-Chip Power (W)  | 0.072        |
| Design Power Budget (W)  | Unspecified* |
| Power Budget Margin (W)  | NA           |
| Dynamic (W)              | 0.002        |
| Device Static (W)        | 0.070        |
| Effective TJA (C/W)      | 4.8          |
| Max Ambient (C)          | 84.7         |
| Junction Temperature (C) | 25.3         |
| Confidence Level         | Low          |
| Setting File             | ---          |
| Simulation Activity File | ---          |
| Design Nets Matched      | NA           |
+--------------------------+--------------+


2. Settings
-----------

+-----------------------+------------+
| Ambient Temp (C)      | 25.0       |
+-----------------------+------------+


3.1 By Hierarchy
----------------

+--------------------------+-----------+
| Name                     | Power (W) |
+--------------------------+-----------+
| TOP_MODULE               |     0.002 |
|   DUT                    |     0.001 |
|   MIDDLEWARE             |     0.001 |
|   UART_MOD               |     0.000 |
+--------------------------+-----------+
"""
)


@pytest.fixture(autouse=True)
def vivado_path(tmp_path: Path):
    path = tmp_path / "arty7"
    path.mkdir()
    (path / "TOP_MODULE_timing_summary_routed.rpt").write_text(TIMING_REPORT)
    (path / "TOP_MODULE_utilization_placed.rpt").write_text(UTILIZATION_REPORT)
    (path / "TOP_MODULE_power_routed.rpt").write_text(POWER_REPORT)
    yield path


@pytest.fixture(autouse=True)
def temp_path():
    path = get_path_to_project("temp_reports") / "vivado"
    if path.exists():
        rmtree(path)
    yield path


def test_copy_report_files_not_found(vivado_path: Path, temp_path: Path):
    try:
        copy_vivado_implementation_results(vivado_path, temp_path)
    except FileNotFoundError:
        assert True
    else:
        assert False


def test_extract_timing_report(vivado_path: Path):
    summary = VivadoTimingSummary.from_rpt(vivado_path)

    assert type(summary) == VivadoTimingSummary
    assert summary.device == "7a35ti-csg324"
    assert summary.tns == 0.0
    assert summary.tpws == 0.0
    assert summary.whs == 0.117
    assert summary.wns == 0.759
    assert summary.wpws == 4.5


def test_extract_utilization_report(vivado_path: Path):
    summary = VivadoUtilizationSummary.from_rpt(vivado_path)

    assert type(summary) == VivadoUtilizationSummary
    assert summary.device == "xc7a35ticsg324-1L"
    assert summary.bram_tiles_used == 0
    assert summary.bram_tiles_available == 50
    assert summary.slice_luts_used == 636
    assert summary.slice_luts_available == 20800
    assert summary.registers_used == 1186
    assert summary.registers_available == 41600


def test_extract_power_report(vivado_path: Path):
    summary = VivadoPowerReport.from_rpt(vivado_path)
    assert type(summary) == VivadoPowerReport
    assert summary.summary.device == "xc7a35ticsg324-1L"
    assert summary.summary.total_on_chip_power_w == 0.072
    assert len(summary.hierarchy) == 4


def test_extract_all_metrics(vivado_path: Path):
    summary = VivadoMetrics.from_rpt(vivado_path)
    assert type(summary) == VivadoMetrics
    assert summary.device == "xc7a35ticsg324-1L"
    assert summary.timing.tns == 0.0
    assert summary.timing.tpws == 0.0
    assert summary.power_summary.total_on_chip_power_w == 0.072
    assert len(summary.power_hierarchy) == 4
