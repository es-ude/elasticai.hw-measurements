from pathlib import Path


class BitstreamReader:
    """Reading the content of bitstream files of different FPGA vendors as bytes, e.g. for writing them into the flash of the FPGA"""

    VENDORS = ("amd", "lattice", "cologne_chip")
    AMD_PADDING = b"\xff" * 12
    AMD_SYNC_WORD = b"\xaa\x99\x55\x66"

    @staticmethod
    def _read_file(path_to_bitstream_file: Path | str, suffixes: tuple[str, ...], hint: str) -> bytes:
        path = Path(path_to_bitstream_file)
        if path.suffix.lower() not in suffixes:
            raise ValueError(
                f"Bitstream file must have the extension {' or '.join(suffixes)} ({hint}), got '{path.name}'"
            )
        data = path.read_bytes()
        if len(data) == 0:
            raise ValueError(f"Bitstream file '{path.name}' is empty")
        return data

    @classmethod
    def read_amd(cls, path_to_bitstream_file: Path | str, remove_header: bool = True) -> bytes:
        """Reading the content of a bitstream file (*.bit, *.bin) compiled from AMD Vivado for AMD FPGAs
        :param path_to_bitstream_file:      Path to the bitstream file (*.bin without header needs `write_bitstream -bin_file`)
        :param remove_header:               Boolean for removing the header information of the *.bit file (everything before the padding words)
        :return:                            Byte array with flash content
        """
        data = cls._read_file(path_to_bitstream_file, (".bin", ".bit"), "AMD Vivado")
        if not remove_header:
            return data

        pos_padding = data.find(cls.AMD_PADDING)
        if pos_padding == -1:
            raise ValueError("No padding words found, it is not a bitstream of an AMD FPGA")
        if data.find(cls.AMD_SYNC_WORD, pos_padding) == -1:
            raise ValueError("Sync word not found, it is not a bitstream of an AMD FPGA")
        return data[pos_padding:]

    @classmethod
    def read_lattice(cls, path_to_bitstream_file: Path | str) -> bytes:
        """Reading the content of a bitstream file (*.bin) compiled for Lattice FPGAs
        :param path_to_bitstream_file:      Path to the bitstream file
        :return:                            Byte array with flash content
        """
        return cls._read_file(path_to_bitstream_file, (".bin",), "binary format of Lattice")

    @classmethod
    def read_cologne_chip(cls, path_to_bitstream_file: Path | str) -> bytes:
        """Reading the content of a bitstream file (*.bit, e.g. design_00.cfg.bit) compiled for Cologne Chip GateMate FPGAs
        The binary file is created by `gmpack --bit`, the ASCII file (*.cfg) is not a valid content for the flash
        :param path_to_bitstream_file:      Path to the bitstream file
        :return:                            Byte array with flash content
        """
        return cls._read_file(
            path_to_bitstream_file, (".bit",), "binary format of GateMate, not the ASCII *.cfg"
        )

    @classmethod
    def read(cls, vendor: str, path_to_bitstream_file: Path | str, **kwargs) -> bytes:
        """Reading the content of a bitstream file of the selected FPGA vendor
        :param vendor:                      String with the vendor of the FPGA: "amd", "lattice" or "cologne_chip"
        :param path_to_bitstream_file:      Path to the bitstream file
        :param kwargs:                      Further options of the reader of the vendor (e.g. remove_header for AMD)
        :return:                            Byte array with flash content
        """
        readers = {
            "amd": cls.read_amd,
            "lattice": cls.read_lattice,
            "cologne_chip": cls.read_cologne_chip,
        }
        if vendor not in readers:
            raise ValueError(f"Unknown FPGA vendor '{vendor}', use one of {cls.VENDORS}")
        return readers[vendor](path_to_bitstream_file, **kwargs)


def write_into_bitstream_file(path_to_file: Path, data: bytes) -> None:
    """Writing the FPGA flash data into new bitstream file (*.bit, *.bin)
    :param path_to_file:    Path to the new generated bitstream file
    :param data:            Byte array with flash content
    :return:                None
    """
    if path_to_file.suffix not in [".bin", ".bit"]:
        raise ValueError("Bit file must be in binary format")

    with open(path_to_file, "wb") as f:
        f.write(data)


def write_into_bitstream_text(path_to_file: Path, data: bytes, add_lines: bool = True) -> None:
    """Writing the FPGA flash into text file in order to read content
    :param path_to_file:    Path to the new generated bitstream file
    :param data:            Byte array with flash content
    :param add_lines:       Boolean for adding line numbers into text file
    :return:                None
    """
    new_file = path_to_file.with_suffix(".txt")
    symbol_per_line = 16
    with open(new_file, "w") as f:
        for i in range(0, len(data), symbol_per_line):
            chunk = data[i : i + symbol_per_line]
            hex_bytes = " ".join(f"{b:02X}" for b in chunk)
            if add_lines:
                f.write(f"{int(i / symbol_per_line):08X}  {hex_bytes}\n")
            else:
                f.write(f"{hex_bytes}\n")


def write_bitstream_into_cheader(path_to_file: Path, data: bytes, symbol_per_line: int = 8) -> None:
    new_file = path_to_file.with_suffix(".h")
    with open(new_file, "w") as f:
        f.write(f"""#include <string.h>
#include <stdio.h>

const uint8_t bitstream[{len(data)}] = {{
""")

        for i in range(0, len(data), symbol_per_line):
            chunk = data[i : i + symbol_per_line]
            hex_bytes = ", ".join(f"0x{b:02X}" for b in chunk)
            f.write(f"\t{hex_bytes}, \n")
        f.write("""};""")
