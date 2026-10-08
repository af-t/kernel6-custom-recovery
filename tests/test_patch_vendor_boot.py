import importlib.util
import os
import struct
import unittest

_script = os.path.join(os.path.dirname(__file__), "..", "scripts", "patch-vendor-boot.py")
_spec = importlib.util.spec_from_file_location("pvb", _script)
pvb = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(pvb)


def make_image(frags, types=(1, 2), dtb=b"\xd0\x0d\xfe\xed" + b"\0" * 100, bootconfig=b"a=b\n"):
    header = bytearray(4096)
    header[0:8] = b"VNDRBOOT"
    struct.pack_into("<II", header, 8, 4, 4096)
    struct.pack_into("<I", header, 24, sum(len(f) for f in frags))
    struct.pack_into("<I", header, 2096, 2128)
    struct.pack_into("<I", header, 2100, len(dtb))
    struct.pack_into("<4I", header, 2112, 108 * len(frags), len(frags), 108, len(bootconfig))
    body = b"".join(frags)
    table = bytearray()
    off = 0
    for f, t in zip(frags, types):
        table += struct.pack("<3I", len(f), off, t) + b"rec\0" + b"\0" * 28 + bytes(16 * 4)
        off += len(f)
    pad = lambda b: b + b"\0" * ((4096 - len(b) % 4096) % 4096)
    return bytes(header) + pad(body) + pad(dtb) + pad(bytes(table)) + pad(bootconfig)


class TestPatchVendorBoot(unittest.TestCase):
    def test_noop_is_byte_identical(self):
        img = make_image([b"A" * 5000, b"B" * 3000])
        out, old = pvb.repack(img, b"B" * 3000)
        self.assertEqual(out, img)
        self.assertEqual(old, 3000)

    def test_replace_resizes_and_reparses(self):
        img = make_image([b"A" * 5000, b"B" * 3000])
        out, _ = pvb.repack(img, b"C" * 7000)
        p = pvb.parse(out)
        self.assertEqual([e[0] for e in p["entries"]], [5000, 7000])
        self.assertEqual([e[1] for e in p["entries"]], [0, 5000])
        self.assertEqual([e[2] for e in p["entries"]], [1, 2])
        self.assertEqual(out[4096:4096 + 5000], b"A" * 5000)
        self.assertEqual(out[4096 + 5000:4096 + 12000], b"C" * 7000)
        self.assertLessEqual(len(out), pvb.PARTITION_SIZE)

    def test_missing_recovery_fails(self):
        img = make_image([b"A" * 100], types=(1,))
        with self.assertRaises(ValueError):
            pvb.repack(img, b"B" * 100)

    def test_oversize_fails(self):
        img = make_image([b"A" * 100, b"B" * 100])
        with self.assertRaises(ValueError):
            pvb.repack(img, b"C" * (pvb.PARTITION_SIZE + 1))

    def test_bad_magic_fails(self):
        with self.assertRaises(ValueError):
            pvb.parse(b"NOTABOOT" + b"\0" * 5000)

    def test_extract_returns_recovery_fragment(self):
        img = make_image([b"A" * 5000, b"B" * 3000])
        self.assertEqual(pvb.extract(img), b"B" * 3000)


if __name__ == "__main__":
    unittest.main()
