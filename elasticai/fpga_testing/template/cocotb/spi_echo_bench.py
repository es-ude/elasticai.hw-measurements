import random
from functools import partial

import cocotb
from cocotb_funcs import (
    build_frame,
    led_is_on,
    spi_transmission,
    split_frame,
    start_clock_and_reset,
)

BITS = (2, 6, 16)

CMD_CNTL = 0
CMD_WRITE = 1
CMD_READ = 2

ADR_START = 0b000001
ADR_SELECT_DUT = 0b000010
ADR_LED_SET = 0b000100
ADR_LED_TOGGLE = 0b001000

NUM_TESTS = 8

frame = partial(build_frame, bits=BITS)


@cocotb.test()
async def top_module(dut):
    dut.SPI_CSN.value = 1
    dut.SPI_MOSI.value = "Z"
    dut.SPI_SCLK.value = 0
    await start_clock_and_reset(dut)

    await spi_transmission(dut, frame(CMD_CNTL, ADR_LED_SET, 1))
    assert led_is_on(dut)

    await spi_transmission(dut, frame(CMD_CNTL, ADR_SELECT_DUT, 0b10))

    for _ in range(NUM_TESTS):
        data_tx = random.getrandbits(BITS[2])

        await spi_transmission(dut, frame(CMD_WRITE, 0, data_tx))
        await spi_transmission(dut, frame(CMD_CNTL, ADR_START, 0))
        assert int(dut.FPGA_BUSY.value) == 0

        await spi_transmission(dut, frame(CMD_READ, 0, 0))
        frame_rx = await spi_transmission(dut, frame(CMD_READ, 0, 0))

        assert split_frame(frame_rx, BITS) == (CMD_READ, 0, data_tx)

    await spi_transmission(dut, frame(CMD_CNTL, ADR_LED_SET, 0))
    assert not led_is_on(dut)
