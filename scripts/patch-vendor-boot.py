#!/usr/bin/env python3
"""Replace the RECOVERY ramdisk fragment of a stock vendor_boot v4 image.

Usage: patch-vendor-boot.py <stock.img> <recovery-frag.bin> <out.img>
       patch-vendor-boot.py --extract <stock.img> <out-frag.bin>

Reads <stock.img>, swaps the single type-2 (RECOVERY) fragment with the
bytes from <recovery-frag.bin>, rebuilds the container and writes <out.img>.
The stock AVB vbmeta+footer is intentionally not carried over: any content
change invalidates the Transsion signature, so output relies on flashing
with verification disabled (Magisk/KSU/AnyKernel3 flow). Fails if output
would exceed the vendor_boot partition size.
"""

import struct
import sys

PAGE = 4096
HEADER_LEN = 2128
ENTRY_LEN = 108
RECOVERY_TYPE = 2
PARTITION_SIZE = 67108864


def _align(n, a=PAGE):
    return (n + a - 1) // a * a


def parse(img):
    if img[0:8] != b"VNDRBOOT":
        raise ValueError("not a VNDRBOOT image")
    ver, psz = struct.unpack("<II", img[8:16])
    if ver != 4 or psz != PAGE:
        raise ValueError(f"unsupported header: version={ver} pagesize={psz}")
    rsize = struct.unpack("<I", img[24:28])[0]
    hsize = struct.unpack("<I", img[2096:2100])[0]
    dtbsize = struct.unpack("<I", img[2100:2104])[0]
    if hsize != HEADER_LEN:
        raise ValueError(f"unexpected header_size={hsize}")
    tsize, tnum, tesize, bcsize = struct.unpack("<4I", img[2112:2128])
    if tesize != ENTRY_LEN:
        raise ValueError(f"unexpected table entry size={tesize}")
    r_end = PAGE + _align(rsize)
    d_end = r_end + _align(dtbsize)
    entries = []
    for i in range(tnum):
        e = img[d_end + i * tesize:d_end + (i + 1) * tesize]
        sz, off, typ = struct.unpack("<3I", e[:12])
        entries.append((sz, off, typ, e[12:44], e[44:108]))
    t_end = d_end + _align(tsize)
    bootconfig = img[t_end:t_end + bcsize]
    return {
        "header": img[:PAGE],
        "rsize": rsize,
        "dtb": img[r_end:d_end],
        "entries": entries,
        "bootconfig": bootconfig,
        "unsigned_end": t_end + _align(bcsize),
    }


def build(p, frags):
    header = bytearray(p["header"])
    struct.pack_into("<I", header, 24, sum(len(f) for f in frags))
    sections = [bytes(header)]
    body = b"".join(frags)
    sections.append(body + b"\0" * (_align(len(body)) - len(body)))
    sections.append(p["dtb"] + b"\0" * (_align(len(p["dtb"])) - len(p["dtb"])))
    table = bytearray()
    off = 0
    for f, (_, _, typ, name, board) in zip(frags, p["entries"]):
        table += struct.pack("<3I", len(f), off, typ) + name + board
        off += len(f)
    sections.append(bytes(table) + b"\0" * (_align(len(table)) - len(table)))
    bc = p["bootconfig"]
    sections.append(bc + b"\0" * (_align(len(bc)) - len(bc)))
    return b"".join(sections)


def repack(stock, new_recovery):
    p = parse(stock)
    idx = [i for i, e in enumerate(p["entries"]) if e[2] == RECOVERY_TYPE]
    if len(idx) != 1:
        raise ValueError(f"expected 1 RECOVERY fragment, found {len(idx)}")
    frags = []
    for i, e in enumerate(p["entries"]):
        start = PAGE + e[1]
        frags.append(new_recovery if i == idx[0] else stock[start:start + e[0]])
    out = build(p, frags)
    if len(out) > PARTITION_SIZE:
        raise ValueError(f"output {len(out)} exceeds partition {PARTITION_SIZE}")
    return out, p["entries"][idx[0]][0]


def extract(stock):
    p = parse(stock)
    idx = [i for i, e in enumerate(p["entries"]) if e[2] == RECOVERY_TYPE]
    if len(idx) != 1:
        raise ValueError(f"expected 1 RECOVERY fragment, found {len(idx)}")
    e = p["entries"][idx[0]]
    start = PAGE + e[1]
    return stock[start:start + e[0]]


def main(argv):
    if len(argv) == 4 and argv[1] == "--extract":
        blob = extract(open(argv[2], "rb").read())
        open(argv[3], "wb").write(blob)
        print(f"extracted recovery fragment: {len(blob)} bytes")
        return
    if len(argv) != 4:
        sys.exit("usage: patch-vendor-boot.py <stock.img> <recovery-frag.bin> <out.img>\n"
                 "       patch-vendor-boot.py --extract <stock.img> <out-frag.bin>")
    stock = open(argv[1], "rb").read()
    blob = open(argv[2], "rb").read()
    out, old_size = repack(stock, blob)
    open(argv[3], "wb").write(out)
    print(f"recovery fragment: {old_size} -> {len(blob)} bytes; output {len(out)} bytes (limit {PARTITION_SIZE})")


if __name__ == "__main__":
    main(sys.argv)
