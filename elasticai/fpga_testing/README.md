# Framework for Hardware Characterization 
This Python package provides APIs for testing Verilog code on FPGAs. This repo includes templates for different devices and Python code in order to test them.
This is also part of the elasticAI ecosystem for deploying deep learning techniques on heterogeneous platform (MCU+FPGA/ASIC). 

## Installation - Third-Party Code
The bitstreams are generated with open-source tools, which are provided by ``devenv`` (see `fpga.nix`). After initialization and starting ``devenv shell``, the environment checks if they are installed:
- Lattice ICE40UP5K and CologneChip GateMate A1: OSS CAD Suite. If it is missing, install it with the command `download_oss_cad` in the ``devenv`` shell (`check_oss_cad_available` shows if a newer version is available).
- AMD Artix-7 and Spartan-7: openXC7 (Yosys, nextpnr-xilinx, Project X-Ray), which is installed by Nix.

For the simulation with cocotb, Icarus Verilog (`iverilog`) is necessary.

## Supported FPGA devices in the workflow
- [x] Lattice ICE40UP5K (SG48)
- [x] CologneChip CCGM1A1
- [x] AMD Spartan-7 S50
- [x] AMD Artix-7 100T (Arty A7)
- [ ] AMD Spartan-7 S15 (WIP)

## Building FPGA designs for testing
We provide a basic structure for testing FPGA designs on

| Board | Function for copying the design | `DEVICE` / `PACKAGE` in the `Makefile` |
|-------|---------------------------------|-----------------------------------------|
| Digilent Arty-A7 ([Link](https://digilent.com/reference/programmable-logic/arty-a7/start?srsltid=AfmBOoqeya_KoM1qKi6M-j7AMEs77-xNVkFL-W1l7ACA632gUgNiiGkL)) | `copy_design_arty7_files()` | `S7` / `xc7a100tcsg324-1` |
| UDE-IES elasticAI.hardware V5 ([Link](https://github.com/es-ude/elastic-ai.hardware/tree/master/v5/revision_2)) | `copy_design_env5_files()` | `S7` / `xc7s50ftgb196-1` |
| UDE-IES elasticAI.hardware v6 mini ([Link](https://github.com/es-ude/elastic-ai.hardware/tree/master/v6)) | `copy_design_env6mini_files()` | `UP5K` / `sg48` |

## How to init the project
Please enter the following codes into the Python terminal in order to initialize the project structure into your project path (once at initialization):
```python
from elasticai.fpga_testing import init_project_folder, copy_oss_cad_scripts

init_project_folder()
copy_oss_cad_scripts()
```
As default value, the destination (arguments in both functions) are the project folder which includes a ```pyproject.toml``` file.

`copy_oss_cad_scripts()` updates the scripts (`scripts/*.mk`) on every call. The main files `Makefile`, `fpga.nix`, `devenv.nix` and `devenv.yaml` are only copied if they do not exist, so your settings (e.g. `DEVICE`, `TOP`, `FREQ`) are kept. Delete a file to get the current template again.

In order to get the design files for a specific device (e.g. for ENV5 with AMD Spartan-7), you have to enter this:
```python
from elasticai.fpga_testing import copy_design

copy_design.copy_design_env5_files()
```
The design files are copied into the folder `designs` (together with the cocotb tests, see below).

## Building the bitstream
Set `DEVICE`, `PACKAGE`, `TOP` and `FREQ` of your board in the `Makefile` of the project (see the table above) and build the bitstream in the ``devenv`` shell:
```bash
make bitstream
```
The result is available in the folder `build` (`TOP_MODULE.bit` for AMD, `TOP_MODULE.bin` for Lattice). Further targets are `synthesize`, `flash` (using openFPGALoader) and `clean`.

For each release of this repo, the CI builds the bitstreams of the three boards above with the template designs and attaches them to the release (`bitstream-<board>-<tag>.<bit|bin>`).

## Simulating the design with cocotb
The functions `copy_design_arty7_files()`, `copy_design_env5_files()` and `copy_design_env6mini_files()` copy the cocotb tests together with the design files. The tests are written into the folder `tests` next to the design folder (or into the folder given with `dest_tests`):
- `cocotb_funcs.py`: Generic functions used by all testbenches (clock and reset, building/splitting frames, UART and SPI transmission)
- `uart_echo_bench.py`, `uart_led_bench.py` (Arty A7) or `spi_echo_bench.py`, `spi_led_bench.py` (ENV5, ENV6.mini): cocotb testbenches (Echo-DUT and LED control). The commands, addresses and bitwidths of the protocol are defined at the top of each testbench, so they can be changed there
- `<board>_test.py`: pytest runner which simulates all Verilog files of the folder `designs` with each testbench (marker `simulation`)

```python
from elasticai.fpga_testing import copy_design

copy_design.copy_design_env6mini_files()
```
```bash
uv run pytest tests/env6_mini_test.py
```
The runner uses the marker `simulation` and needs Icarus Verilog.
The design of the ENV6.mini uses the iCE40 primitive `SB_GB` as clock buffer. It is bypassed in the simulation with the define `SIMULATION` (set by the runner `env6_mini_test.py`).
