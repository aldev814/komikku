#!/usr/bin/env python3
"""Audit 64-bit ELF LOAD and uncompressed ZIP alignment; does not replace device testing."""
import argparse
import hashlib
import json
import struct
import zipfile
from pathlib import Path

PAGE_SIZE = 16384


def inspect_elf(data):
    if data[:4] != b"\x7fELF" or data[4] != 2:
        raise ValueError("Expected an ELF64 library")
    endian = "<" if data[5] == 1 else ">"
    offset = struct.unpack_from(endian + "Q", data, 32)[0]
    entry_size, count = struct.unpack_from(endian + "HH", data, 54)
    if entry_size < 56 or offset + entry_size * count > len(data):
        raise ValueError("Invalid ELF program header bounds")
    loads, relro_ends = [], []
    for index in range(count):
        kind, flags, file_offset, address, _, file_size, memory_size, alignment = struct.unpack_from(
            endian + "IIQQQQQQ", data, offset + index * entry_size
        )
        if kind == 1:
            loads.append({
                "alignment": alignment,
                "congruent_16k": file_offset % PAGE_SIZE == address % PAGE_SIZE,
            })
        elif kind == 0x6474E552:
            # Informational: RELRO layout needs separate runtime/linker validation.
            relro_ends.append((address + memory_size) % PAGE_SIZE)
    return {
        "loads": loads,
        "load_aligned_16k": bool(loads) and all(
            row["alignment"] >= PAGE_SIZE and row["congruent_16k"] for row in loads
        ),
        "relro_end_mod_16k": relro_ends,
    }


def inspect_apk(path):
    rows = []
    with path.open("rb") as raw, zipfile.ZipFile(path) as archive:
        for info in archive.infolist():
            if not info.filename.endswith(".so") or not info.filename.startswith(("lib/arm64-v8a/", "lib/x86_64/")):
                continue
            row = {"library": info.filename, **inspect_elf(archive.read(info))}
            raw.seek(info.header_offset)
            header = raw.read(30)
            if header[:4] != b"PK\x03\x04":
                raise ValueError("Invalid ZIP local header")
            name_length, extra_length = struct.unpack_from("<HH", header, 26)
            data_offset = info.header_offset + 30 + name_length + extra_length
            row["compressed"] = info.compress_type != zipfile.ZIP_STORED
            row["zip_aligned_16k"] = row["compressed"] or data_offset % PAGE_SIZE == 0
            rows.append(row)
    return {
        "apk": path.name,
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "passed": bool(rows) and all(r["load_aligned_16k"] and r["zip_aligned_16k"] for r in rows),
        "libraries": rows,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("apk", type=Path)
    args = parser.parse_args()
    report = inspect_apk(args.apk)
    print(json.dumps(report, indent=2))
    raise SystemExit(0 if report["passed"] else 1)


if __name__ == "__main__":
    main()
