# Framework for Hardware Characterization 
This Python package provides APIs for testing Verilog code on FPGAs. This repo includes templates for different devices and Python code in order to test them.
This is also part of the elasticAI ecosystem for deploying deep learning techniques on heterogeneous platform (MCU+FPGA/ASIC). 

## Installation - Third-Party Code
For generating the bitstream for the FPGAs (actual only ChipCologne GateMate A1 and Lattice ICE40UP5K are supported), the OSS-CAD suite is used. After initialization and starting ``devenv``, the env checks, if it is installed. It not, you will get the information.

## Supported FPGA devices in the workflow
- [x] Lattice ICE40UP5K (SG48)
- [x] CologneChip CCGM1A1
- [x] AMD Spartan-7 S50 
- [ ] AMD Spartan-7 S15 (WIP)

## Building FPGA designs for testing
We will provide a basic structure for testing FPGA designs on
1. Digilent Arty-A7 boards ([Link](https://digilent.com/reference/programmable-logic/arty-a7/start?srsltid=AfmBOoqeya_KoM1qKi6M-j7AMEs77-xNVkFL-W1l7ACA632gUgNiiGkL))
2. UDE-IES elasticAI.hardware V5 ([Link](https://github.com/es-ude/elastic-ai.hardware/tree/master/v5/revision_2))
3. UDE-IES elasticAI.hardware v6 ([Link](https://github.com/es-ude/elastic-ai.hardware/tree/master/v6))

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

## Simulating the design with cocotb
The functions `copy_design_arty7_files()`, `copy_design_env5_files()` and `copy_design_env6mini_files()` copy the cocotb tests together with the design files. The tests are written into the folder `tests` next to the design folder (or into the folder given with `dest_tests`):
- `cocotb_funcs.py`: Generic functions used by all testbenches (clock and reset, building/splitting frames, UART and SPI transmission)
- `uart_echo_bench.py`, `uart_led_bench.py` (Arty A7) or `spi_echo_bench.py`, `spi_led_bench.py` (ENV5, ENV6.mini): cocotb testbenches (Echo-DUT and LED control). The commands, addresses and bitwidths of the protocol are defined at the top of each testbench, so they can be changed there
- `test_<board>.py`: pytest runner which simulates all Verilog files of the folder `designs` with each testbench (marker `simulation`)

```python
from elasticai.fpga_testing import copy_design

copy_design.copy_design_env6mini_files()
```
```bash
uv run pytest tests/test_env6_mini.py
```
The design of the ENV6.mini uses the iCE40 primitive `SB_GB` as clock buffer. It is bypassed in the simulation with the define `SIMULATION` (set by the runner `test_env6_mini.py`).
