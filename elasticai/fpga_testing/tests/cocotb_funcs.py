import cocotb
from cocotb.triggers import ClockCycles, RisingEdge
from cocotb.clock import Clock


PERIOD_NS = 10


async def init_dut(dut):
    dut.CLK_100MHz.value = 0
    dut.RSTN.value = 0
    dut.SPI_MOSI.value = "Z"
    dut.SPI_SCLK.value = 0
    dut.SPI_CSN.value = 1

    cocotb.start_soon(Clock(dut.CLK_SYS_EXT, PERIOD_NS, unit="ns").start())
    for _ in range(4):
        await RisingEdge(dut.CLK_100MHz)


async def reset_dut(dut, cycles_rst: int = 4):
    for _ in range(2):
        dut.RSTN.value = 0
        await ClockCycles(dut.CLK_100MHz, cycles_rst)
        dut.RSTN.value = 1
        await ClockCycles(dut.CLK_100MHz, cycles_rst)
        
    for _ in range(16):
        await RisingEdge(dut.CLK_100MHz)


async def spi_transmission(dut, reg: bytes, data: bytes, spi_clk: int=4, bitwidth: int=24) -> str:
    def bytes_to_bitstring(data: bytes) -> str:
        return "".join(f"{byte:08b}" for byte in data)

    return_data = list()
    assert len(data) + len(reg) == int(bitwidth / 8)

    dut.SPI_CSN.value = 0
    await ClockCycles(dut.CLK_100MHz, 1)
    for val in bytes_to_bitstring(reg + data):
        dut.SPI_MOSI.value = int(val)

        dut.SPI_SCLK.value = 1
        await ClockCycles(dut.CLK_100MHz, spi_clk, RisingEdge)
        return_data.append(int(dut.SPI_MISO.value))
        dut.SPI_SCLK.value = 0
        await ClockCycles(dut.CLK_100MHz, spi_clk, RisingEdge)

    dut.SPI_MOSI.value = "Z"
    dut.SPI_CSN.value = 1
    await ClockCycles(dut.CLK_100MHz, 20)

    return bytes(
        int("".join(str(b) for b in return_data[i:i + 8]), 2)
        for i in range(0, len(return_data), 8)
    )
