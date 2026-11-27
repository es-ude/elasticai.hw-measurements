import unittest
from contextlib import chdir
from pathlib import Path
from shutil import rmtree

import pytest

from elasticai.fpga_testing import get_path_to_project

from .bin_build import (
    BitstreamReader,
    write_bitstream_into_cheader,
    write_into_bitstream_file,
    write_into_bitstream_text,
)

PAYLOAD = b"\xff" * 32 + b"\x00\x00\x00\xbb\x11\x22\x00\x44" + b"\xaa\x99\x55\x66" + bytes(range(64))


def _write(tmp_path, name: str, content: bytes):
    path = tmp_path / name
    path.write_bytes(content)
    return path


def test_amd_bit_file_header_is_removed(tmp_path):
    header = b"\x00\x09\x0f\xf0\x0f\xf0\x0f\xf0\x0f\xf0\x00\x01a\x00\x0adesign;UTF\x00e\x00\x00\x00\x60"
    path = _write(tmp_path, "design.bit", header + PAYLOAD)

    assert BitstreamReader.read_amd(path) == PAYLOAD
    assert BitstreamReader.read_amd(path, remove_header=False) == header + PAYLOAD


def test_amd_bin_file_stays_unchanged(tmp_path):
    path = _write(tmp_path, "design.bin", PAYLOAD)

    assert BitstreamReader.read_amd(str(path)) == PAYLOAD


def test_amd_rejects_files_without_padding_or_sync_word(tmp_path):
    with pytest.raises(ValueError, match="padding"):
        BitstreamReader.read_amd(_write(tmp_path, "a.bit", b"\x01" * 100))
    with pytest.raises(ValueError, match="Sync word"):
        BitstreamReader.read_amd(_write(tmp_path, "b.bit", b"\xff" * 32 + b"\x01" * 100))


def test_lattice_accepts_only_bin_files(tmp_path):
    assert (
        BitstreamReader.read_lattice(_write(tmp_path, "design.bin", b"\x7e\xaa\x99\x7e"))
        == b"\x7e\xaa\x99\x7e"
    )
    with pytest.raises(ValueError, match="extension"):
        BitstreamReader.read_lattice(_write(tmp_path, "design.bit", b"\x7e\xaa\x99\x7e"))


def test_cologne_chip_accepts_binary_bit_file_but_not_the_ascii_cfg(tmp_path):
    content = bytes([0xD9, 0x01, 0xED, 0x00])

    assert BitstreamReader.read_cologne_chip(_write(tmp_path, "blink_00.cfg.bit", content)) == content
    with pytest.raises(ValueError, match="ASCII"):
        BitstreamReader.read_cologne_chip(_write(tmp_path, "blink_00.cfg", b"D9 01 ED 00\n"))


def test_empty_files_are_rejected(tmp_path):
    with pytest.raises(ValueError, match="empty"):
        BitstreamReader.read_lattice(_write(tmp_path, "design.bin", b""))


def test_read_selects_the_reader_of_the_vendor(tmp_path):
    path = _write(tmp_path, "design.bin", PAYLOAD)

    assert BitstreamReader.read("amd", path) == PAYLOAD
    assert BitstreamReader.read("lattice", path) == PAYLOAD
    assert BitstreamReader.read("amd", path, remove_header=False) == PAYLOAD
    with pytest.raises(ValueError, match="Unknown FPGA vendor"):
        BitstreamReader.read("xilinx", path)


class TestBitStreamTranslator(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.path_to_temp = Path(get_path_to_project("temp_build"))
        if cls.path_to_temp.exists():
            rmtree(cls.path_to_temp)
        cls.path_to_temp.mkdir(parents=True, exist_ok=True)

        cls.path_to_template = cls.path_to_temp / "template"
        cls.path_to_template.mkdir(parents=True, exist_ok=True)
        header = b"\x00\x09\x0f\xf0\x0f\xf0\x0f\xf0\x0f\xf0\x00\x00\x01a\x00\x0bTOP_MODULE\x00"
        payload = bytes(range(256)) * 4
        (cls.path_to_template / "TOP_MODULE.bit").write_bytes(
            header + BitstreamReader.AMD_PADDING + BitstreamReader.AMD_SYNC_WORD + payload
        )

    @classmethod
    def tearDownClass(cls):
        pass

    def test_write_bin_file_with_header_absolute(self):
        data = BitstreamReader().read_amd(
            path_to_bitstream_file=self.path_to_template / "TOP_MODULE.bit", remove_header=False
        )
        write_into_bitstream_file(path_to_file=self.path_to_temp / "TOP_MODULE_0.bin", data=data)
        self.assertTrue((self.path_to_temp / "TOP_MODULE_0.bin").exists())

    def test_write_bin_file_with_header_relative(self):
        data = BitstreamReader().read_amd(
            path_to_bitstream_file=self.path_to_template / "TOP_MODULE.bit", remove_header=False
        )
        with chdir(self.path_to_temp):
            write_into_bitstream_file(path_to_file=Path("TOP_MODULE_R.bin"), data=data)
        self.assertTrue((self.path_to_temp / "TOP_MODULE_R.bin").exists())

    def test_write_text_file_with_header(self):
        data = BitstreamReader().read_amd(
            path_to_bitstream_file=self.path_to_template / "TOP_MODULE.bit", remove_header=False
        )
        write_into_bitstream_text(
            path_to_file=self.path_to_temp / "TOP_MODULE_0.txt", data=data, add_lines=True
        )
        self.assertTrue((self.path_to_temp / "TOP_MODULE_0.txt").exists())
        write_into_bitstream_text(
            path_to_file=self.path_to_temp / "TOP_MODULE_1.txt", data=data, add_lines=False
        )
        self.assertTrue((self.path_to_temp / "TOP_MODULE_1.txt").exists())

    def test_write_text_file_without_header(self):
        data = BitstreamReader().read_amd(
            path_to_bitstream_file=self.path_to_template / "TOP_MODULE.bit", remove_header=True
        )
        write_into_bitstream_text(
            path_to_file=self.path_to_temp / "TOP_MODULE_2.txt", data=data, add_lines=True
        )
        self.assertTrue((self.path_to_temp / "TOP_MODULE_2.txt").exists())
        write_into_bitstream_text(
            path_to_file=self.path_to_temp / "TOP_MODULE_3.txt", data=data, add_lines=False
        )
        self.assertTrue((self.path_to_temp / "TOP_MODULE_3.txt").exists())

    def test_write_bitstream_into_cheader(self):
        filename = "TOP_MODULE.h"
        data = bytes([val for val in range(16)])

        write_bitstream_into_cheader(path_to_file=self.path_to_temp / filename, data=data)
        assert (self.path_to_temp / filename).exists()

        with open((self.path_to_temp / filename).as_posix(), mode="r") as f:
            content = f.read()
            assert (
                content
                == """#include <string.h>
#include <stdio.h>

const uint8_t bitstream[16] = {
	0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 
	0x08, 0x09, 0x0A, 0x0B, 0x0C, 0x0D, 0x0E, 0x0F, 
};"""
            )


if __name__ == "__main__":
    unittest.main()
