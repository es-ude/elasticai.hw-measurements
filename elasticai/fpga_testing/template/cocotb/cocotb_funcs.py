import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge

PERIOD_CLK_NS = 5


def clock_port(dut):
    """Clock input of the top module (CLK_SYS_EXT if the design has an external clock buffer, otherwise CLK_SYS)"""
    return dut.CLK_SYS_EXT if hasattr(dut, "CLK_SYS_EXT") else dut.CLK_SYS


async def clk_cycles(dut, num_cycles: int) -> None:
    """Waiting for a number of rising edges of the system clock"""
    clk = clock_port(dut)
    for _ in range(num_cycles):
        await RisingEdge(clk)


async def start_clock_and_reset(dut, period_ns: int = PERIOD_CLK_NS) -> None:
    """Starting the system clock and applying the reset sequence of the test environment"""
    clk = clock_port(dut)
    clk.value = 0
    dut.RSTN.value = 0
    cocotb.start_soon(Clock(clk, period_ns, unit="ns").start())
    await clk_cycles(dut, 8)
    for idx in range(4):
        await RisingEdge(clk)
        dut.RSTN.value = idx % 2
        await RisingEdge(clk)
    dut.RSTN.value = 1
    await clk_cycles(dut, 2)


def build_frame(cmd: int, adr: int, data: int, bits: tuple[int, int, int]) -> str:
    """Building a frame of the protocol (command, address, data) as bit string (MSB first)
    :param bits:    Number of bits of command, address and data"""
    bits_cmd, bits_adr, bits_data = bits
    frame = (cmd << (bits_adr + bits_data)) | (adr << bits_data) | data
    return f"{frame:0{bits_cmd + bits_adr + bits_data}b}"


def split_frame(frame: str, bits: tuple[int, int, int]) -> tuple[int, int, int]:
    """Splitting a frame of the protocol (bit string, MSB first) into command, address and data
    :param bits:    Number of bits of command, address and data"""
    bits_cmd, bits_adr, _ = bits
    return (
        int(frame[:bits_cmd], 2),
        int(frame[bits_cmd : bits_cmd + bits_adr], 2),
        int(frame[bits_cmd + bits_adr :], 2),
    )


def led_is_on(dut) -> bool:
    return bool(int(dut.LED.value) & 0x01)


def uart_cycles_per_bit(dut) -> int:
    """Number of system clock cycles of one bit on the UART interface"""
    return dut.UART_CNT_BAUDRATE.value.to_unsigned() * dut.UART_MOD.NSAMP.value.to_unsigned()


async def uart_transmission(dut, frame: str, cycles_per_bit: int) -> None:
    """Sending a frame (bit string, MSB first) byte by byte (start bit, 8 data bits LSB first, stop bit) to the DUT"""
    await clk_cycles(dut, cycles_per_bit)
    for idx in range(0, len(frame), 8):
        dut.UART_RX.value = 0
        await clk_cycles(dut, cycles_per_bit)
        for val in frame[idx : idx + 8][::-1]:
            dut.UART_RX.value = int(val)
            await clk_cycles(dut, cycles_per_bit)
        dut.UART_RX.value = 1
        await RisingEdge(dut.uart_mod_rdy)
        await clk_cycles(dut, cycles_per_bit // 2)
    await clk_cycles(dut, cycles_per_bit)


async def spi_transmission(dut, frame: str, cycles_per_sclk: int = 16, cycles_idle: int = 200) -> str:
    """Sending a frame (bit string, MSB first) to the DUT (CPOL = 0, CPHA = 0, MSB first)
    :return:    Bit string with the data received from the DUT (MISO) during the transmission"""
    await clk_cycles(dut, cycles_per_sclk)
    dut.SPI_CSN.value = 0
    await clk_cycles(dut, 4)

    bits_rx = ""
    for bit in frame:
        dut.SPI_MOSI.value = int(bit)
        dut.SPI_SCLK.value = 1
        await clk_cycles(dut, cycles_per_sclk // 2)
        bits_rx += str(int(dut.SPI_MISO.value))
        dut.SPI_SCLK.value = 0
        await clk_cycles(dut, cycles_per_sclk // 2)

    await clk_cycles(dut, 4)
    dut.SPI_MOSI.value = "Z"
    dut.SPI_CSN.value = 1
    await clk_cycles(dut, cycles_idle)
    return bits_rx
