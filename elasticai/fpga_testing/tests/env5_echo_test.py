import random
from copy import deepcopy
from shutil import rmtree

import cocotb
import pytest
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge
from elasticai.creator.testing.cocotb_runner import run_cocotb_sim_for_src_dir

from elasticai.fpga_testing import get_path_to_project
from elasticai.fpga_testing.copy_design import copy_design_env5_files
from elasticai.fpga_testing.tests import cocotb_settings_env5

CMD_CNTL = 0
CMD_WRITE = 1
CMD_READ = 2

ADR_START = 0b000001
ADR_SELECT_DUT = 0b000010
ADR_LED_SET = 0b000100

NUM_CLK_PER_SCLK = 16
NUM_TESTS = 8


async def clk_cycles(dut, num: int) -> None:
    for _ in range(num):
        await RisingEdge(dut.CLK_SYS)


async def spi_frame(dut, bitwidth: int, cmd: int, adr: int, data: int) -> int:
    frame = (cmd << (bitwidth - 2)) | (adr << (bitwidth - 8)) | data
    bits_tx = f"{frame:0{bitwidth}b}"
    bits_rx = ""

    await clk_cycles(dut, NUM_CLK_PER_SCLK)
    dut.SPI_CSN.value = 0
    await clk_cycles(dut, 4)
    for bit in bits_tx:
        dut.SPI_MOSI.value = int(bit)
        dut.SPI_SCLK.value = 1
        await clk_cycles(dut, NUM_CLK_PER_SCLK // 2)
        bits_rx += str(int(dut.SPI_MISO.value))
        dut.SPI_SCLK.value = 0
        await clk_cycles(dut, NUM_CLK_PER_SCLK // 2)
    await clk_cycles(dut, 4)
    dut.SPI_MOSI.value = "Z"
    dut.SPI_CSN.value = 1
    await clk_cycles(dut, 200)
    return int(bits_rx, 2)


@cocotb.test()
async def top_module(dut):
    bitwidth = dut.SPI_BITWIDTH.value.to_unsigned()
    num_bits_data = bitwidth - 8

    dut.CLK_SYS.value = 0
    dut.RSTN.value = 0
    dut.SPI_CSN.value = 1
    dut.SPI_MOSI.value = "Z"
    dut.SPI_SCLK.value = 0

    cocotb.start_soon(Clock(dut.CLK_SYS, 5, unit="ns").start())
    await clk_cycles(dut, 8)
    for idx in range(4):
        await RisingEdge(dut.CLK_SYS)
        dut.RSTN.value = idx % 2
        await RisingEdge(dut.CLK_SYS)
    dut.RSTN.value = 1
    await clk_cycles(dut, 2)

    await spi_frame(dut, bitwidth, CMD_CNTL, ADR_LED_SET, 1)
    assert int(dut.LED.value) & 0x01 == 1

    await spi_frame(dut, bitwidth, CMD_CNTL, ADR_SELECT_DUT, 0b10)

    for _ in range(NUM_TESTS):
        data_tx = random.randint(0, 2**num_bits_data - 1)

        await spi_frame(dut, bitwidth, CMD_WRITE, 0, data_tx)
        await spi_frame(dut, bitwidth, CMD_CNTL, ADR_START, 0)
        assert int(dut.FPGA_BUSY.value) == 0

        await spi_frame(dut, bitwidth, CMD_READ, 0, 0)
        frame_rx = await spi_frame(dut, bitwidth, CMD_READ, 0, 0)

        assert frame_rx >> (bitwidth - 2) == CMD_READ
        assert (frame_rx >> num_bits_data) & 0x3F == 0
        assert frame_rx & (2**num_bits_data - 1) == data_tx

    await spi_frame(dut, bitwidth, CMD_CNTL, ADR_LED_SET, 0)
    assert int(dut.LED.value) & 0x01 == 0


@pytest.mark.simulation
def test_echo_template() -> None:
    cocotb_settings = deepcopy(cocotb_settings_env5)
    cocotb_settings["cocotb_test_module"] = "elasticai.fpga_testing.tests.env5_echo_test"

    run_cocotb_sim_for_src_dir(**cocotb_settings)


@pytest.mark.simulation
def test_echo_build() -> None:
    artefact_dir = get_path_to_project() / "temp_build" / "env5_echo"
    if artefact_dir.exists():
        rmtree(artefact_dir)

    artefact_dir.mkdir(parents=True, exist_ok=True)
    copy_design_env5_files(dest=artefact_dir)

    cocotb_settings = deepcopy(cocotb_settings_env5)
    cocotb_settings["cocotb_test_module"] = "elasticai.fpga_testing.tests.env5_echo_test"
    cocotb_settings["src_files"] = list(artefact_dir.rglob("*.v"))
    run_cocotb_sim_for_src_dir(**cocotb_settings)
