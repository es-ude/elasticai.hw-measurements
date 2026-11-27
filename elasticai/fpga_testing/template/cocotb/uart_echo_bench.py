import random
from functools import partial

import cocotb
from cocotb_funcs import (
    build_frame,
    clk_cycles,
    led_is_on,
    start_clock_and_reset,
    uart_cycles_per_bit,
    uart_transmission,
)

BITS = (2, 6, 16)

CMD_CNTL = 0
CMD_WRITE = 1
CMD_READ = 2

ADR_START = 0b000001
ADR_SELECT_DUT = 0b000010
ADR_LED_SET = 0b000100
ADR_LED_TOGGLE = 0b001000

frame = partial(build_frame, bits=BITS)


@cocotb.test()
async def top_module(dut):
    cycles_per_bit = uart_cycles_per_bit(dut)

    sequence = [
        (frame(CMD_CNTL, ADR_LED_SET, 1), True),
        (frame(CMD_CNTL, ADR_SELECT_DUT, 0b10), True),
    ]
    for _ in range(4):
        sequence.append((frame(CMD_WRITE, 0, random.getrandbits(BITS[2])), True))
        sequence.append((frame(CMD_CNTL, ADR_START, 0), True))
    sequence.append((frame(CMD_CNTL, ADR_LED_SET, 0), False))

    dut.UART_RX.value = 1
    await start_clock_and_reset(dut)

    for frame_tx, state_led in sequence:
        await uart_transmission(dut, frame_tx, cycles_per_bit)
        assert led_is_on(dut) == state_led

    await clk_cycles(dut, cycles_per_bit)
