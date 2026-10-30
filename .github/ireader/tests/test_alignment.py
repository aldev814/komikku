import importlib.util
from pathlib import Path
import struct
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('alignment', ROOT / 'check_apk_alignment.py')
alignment = importlib.util.module_from_spec(spec)
spec.loader.exec_module(alignment)


def elf(page_size=16384, address=0):
    identity = b'\x7fELF' + bytes([2, 1, 1]) + bytes(9)
    header = struct.pack('<16sHHIQQQIHHHHHH', identity, 3, 183, 1, 0, 64, 0, 0, 64, 56, 1, 0, 0, 0)
    return header + struct.pack('<IIQQQQQQ', 1, 5, 0, address, 0, 120, 120, page_size)


class NativeAlignmentTest(unittest.TestCase):
    def apk(self, data, aligned=True, compressed=False, abi='arm64-v8a'):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        path = Path(temporary.name) / 'fixture.apk'
        info = zipfile.ZipInfo('lib/' + abi + '/libfixture.so')
        info.compress_type = zipfile.ZIP_DEFLATED if compressed else zipfile.ZIP_STORED
        if aligned:
            size = (16384 - (30 + len(info.filename.encode()) + 4) % 16384) % 16384
            info.extra = struct.pack('<HH', 0xFFFF, size) + bytes(size)
        with zipfile.ZipFile(path, 'w') as archive:
            archive.writestr(info, data)
        return path

    def test_aligned_library_passes(self):
        self.assertTrue(alignment.inspect_apk(self.apk(elf()))['passed'])

    def test_4k_load_segment_blocks_release(self):
        report = alignment.inspect_apk(self.apk(elf(4096)))
        self.assertFalse(report['passed'])
        self.assertFalse(report['libraries'][0]['load_aligned_16k'])

    def test_noncongruent_load_address_blocks_release(self):
        self.assertFalse(alignment.inspect_apk(self.apk(elf(address=4096)))['passed'])

    def test_unaligned_uncompressed_zip_entry_blocks_release(self):
        report = alignment.inspect_apk(self.apk(elf(), aligned=False))
        self.assertFalse(report['passed'])
        self.assertTrue(report['libraries'][0]['load_aligned_16k'])

    def test_compressed_library_does_not_require_zip_page_alignment(self):
        self.assertTrue(alignment.inspect_apk(self.apk(elf(), aligned=False, compressed=True))['passed'])

    def test_apk_without_64bit_libraries_is_not_a_valid_universal_report(self):
        self.assertFalse(alignment.inspect_apk(self.apk(elf(), abi='armeabi-v7a'))['passed'])

    def test_malformed_library_fails_closed(self):
        with self.assertRaises(ValueError):
            alignment.inspect_apk(self.apk(b'not an ELF file'))
