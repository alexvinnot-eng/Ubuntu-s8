#!/usr/bin/env python3
"""Patch a Halium Android boot image so run-init does not require /dev/console."""

from __future__ import annotations

import gzip
import hashlib
from pathlib import Path
import struct
import sys


def align(value: int, block: int) -> int:
    return (value + block - 1) // block * block


def parse_newc(raw: bytes) -> list[tuple[bytes, list[int], bytes, bytes]]:
    entries = []
    offset = 0
    while offset + 110 <= len(raw):
        magic = raw[offset : offset + 6]
        if magic not in (b"070701", b"070702"):
            raise ValueError(f"bad newc magic at {offset}: {magic!r}")
        values = [int(raw[offset + 6 + i * 8 : offset + 14 + i * 8], 16) for i in range(13)]
        offset += 110
        filesize = values[6]
        namesize = values[11]
        name = raw[offset : offset + namesize]
        if len(name) != namesize or not name.endswith(b"\0"):
            raise ValueError("invalid newc pathname")
        offset = align(offset + namesize, 4)
        data = raw[offset : offset + filesize]
        if len(data) != filesize:
            raise ValueError("truncated newc entry")
        offset = align(offset + filesize, 4)
        entries.append((magic, values, name, data))
        if name == b"TRAILER!!!\0":
            return entries
    raise ValueError("newc trailer not found")


def pack_newc(entries: list[tuple[bytes, list[int], bytes, bytes]]) -> bytes:
    output = bytearray()
    for magic, original_values, name, data in entries:
        values = original_values.copy()
        values[6] = len(data)
        values[11] = len(name)
        if magic == b"070702":
            values[12] = sum(data) & 0xFFFFFFFF
        header = magic + b"".join(f"{value:08x}".encode() for value in values)
        if len(header) != 110:
            raise ValueError("invalid generated newc header")
        output.extend(header)
        output.extend(name)
        output.extend(b"\0" * (-len(output) % 4))
        output.extend(data)
        output.extend(b"\0" * (-len(output) % 4))
    output.extend(b"\0" * (-len(output) % 512))
    return bytes(output)


def patch_init(script: bytes) -> bytes:
    old_validate = b'run-init -n "${rootmnt}" "${1}"'
    new_validate = b'run-init -c /dev/null -n "${rootmnt}" "${1}"'
    old_exec = (
        b'exec run-init ${drop_caps} ${rootmnt} ${init} "$@" '
        b'<${rootmnt}/dev/console >${rootmnt}/dev/console 2>&1'
    )
    new_exec = b'exec run-init -c /dev/null ${drop_caps} ${rootmnt} ${init} "$@"'
    if script.count(old_validate) != 1:
        raise ValueError("unexpected validate_init implementation")
    if script.count(old_exec) != 1:
        raise ValueError("unexpected final run-init implementation")
    result = script.replace(old_validate, new_validate).replace(old_exec, new_exec)
    if b"/dev/console" in result:
        raise ValueError("patched init still references /dev/console")
    return result


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit(f"usage: {sys.argv[0]} INPUT_BOOT OUTPUT_BOOT")
    source = Path(sys.argv[1])
    target = Path(sys.argv[2])
    image = source.read_bytes()
    if image[:8] != b"ANDROID!":
        raise SystemExit("not an Android boot image")

    kernel_size, _, ramdisk_size, _, second_size, _, _, page_size, dt_size, _ = struct.unpack_from(
        "<10I", image, 8
    )
    kernel_offset = page_size
    ramdisk_offset = kernel_offset + align(kernel_size, page_size)
    second_offset = ramdisk_offset + align(ramdisk_size, page_size)
    dt_offset = second_offset + align(second_size, page_size)

    kernel = image[kernel_offset : kernel_offset + kernel_size]
    ramdisk_compressed = image[ramdisk_offset : ramdisk_offset + ramdisk_size]
    second = image[second_offset : second_offset + second_size]
    dt = image[dt_offset : dt_offset + dt_size]
    if len(kernel) != kernel_size or len(ramdisk_compressed) != ramdisk_size or len(dt) != dt_size:
        raise SystemExit("boot image sections are truncated")

    entries = parse_newc(gzip.decompress(ramdisk_compressed))
    patched_count = 0
    patched_entries = []
    for magic, values, name, data in entries:
        if name == b"init\0":
            data = patch_init(data)
            patched_count += 1
        patched_entries.append((magic, values, name, data))
    if patched_count != 1:
        raise SystemExit(f"expected one init entry, found {patched_count}")

    ramdisk = gzip.compress(pack_newc(patched_entries), compresslevel=9, mtime=0)
    header = bytearray(image[:page_size])
    struct.pack_into("<I", header, 16, len(ramdisk))

    digest = hashlib.sha1()
    for data, size in ((kernel, kernel_size), (ramdisk, len(ramdisk)), (second, second_size), (dt, dt_size)):
        digest.update(data)
        digest.update(struct.pack("<I", size))
    header[576:608] = digest.digest() + b"\0" * 12

    output = bytearray(header)
    for data in (kernel, ramdisk, second, dt):
        output.extend(data)
        output.extend(b"\0" * (-len(output) % page_size))
    if len(output) > 40 * 1024 * 1024:
        raise SystemExit("patched boot image exceeds the 40 MiB BOOT partition")
    target.write_bytes(output)
    print(f"old ramdisk: {ramdisk_size} bytes")
    print(f"new ramdisk: {len(ramdisk)} bytes")
    print(f"boot image: {len(output)} bytes")


if __name__ == "__main__":
    main()
