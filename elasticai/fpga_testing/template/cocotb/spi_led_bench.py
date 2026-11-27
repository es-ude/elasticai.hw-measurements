from functools import partial

import cocotb
from cocotb_funcs import (
    build_frame,
    clk_cycles,
    led_is_on,
    spi_transmission,
    start_clock_and_reset,
)

BITS = (2, 6, 16)

CMD_CNTL = 0

ADR_LED_SET = 0b000100
ADR_LED_TOGGLE = 0b001000

frame = partial(build_frame, bits=BITS)

LED_SEQUENCE = [
    (frame(CMD_CNTL, ADR_LED_SET, 1), True),
    (frame(CMD_CNTL, ADR_LED_SET, 0), False),
    (frame(CMD_CNTL, ADR_LED_SET, 1), True),
    (frame(CMD_CNTL, ADR_LED_SET, 0), False),
    (frame(CMD_CNTL, ADR_LED_TOGGLE, 0), True),
    (frame(CMD_CNTL, ADR_LED_TOGGLE, 0), False),
    (frame(CMD_CNTL, ADR_LED_TOGGLE, 0), True),
    (frame(CMD_CNTL, ADR_LED_TOGGLE, 0), False),
]


@cocotb.test()
async def top_module(dut):
    dut.SPI_CSN.value = 1
    dut.SPI_MOSI.value = "Z"
    dut.SPI_SCLK.value = 0
    await start_clock_and_reset(dut)

    for frame_tx, state_led in LED_SEQUENCE:
        await spi_transmission(dut, frame_tx)
        assert led_is_on(dut) == state_led

    await clk_cycles(dut, 16)
