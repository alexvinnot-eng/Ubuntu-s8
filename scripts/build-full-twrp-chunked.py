#!/usr/bin/env python3
"""Build a TWRP ZIP without any archive member larger than 256 MiB.

Older recovery unzip implementations use signed 32-bit counters and cannot
reliably list or extract a single multi-gigabyte ubuntu.img entry.
"""

from __future__ import annotations

import argparse
import hashlib
import os
import zipfile
from pathlib import Path


CHUNK_SIZE = 256 * 1024 * 1024
COPY_SIZE = 1024 * 1024
ZIP_DATE = (2020, 1, 1, 0, 0, 0)


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as source:
        while block := source.read(COPY_SIZE):
            value.update(block)
    return value.hexdigest()


def info(name: str, mode: int = 0o100644) -> zipfile.ZipInfo:
    item = zipfile.ZipInfo(name, ZIP_DATE)
    item.compress_type = zipfile.ZIP_DEFLATED
    item.create_system = 3
    item.external_attr = mode << 16
    return item


def write_bytes(archive: zipfile.ZipFile, name: str, data: bytes, mode: int = 0o100644) -> None:
    item = info(name, mode)
    item.file_size = len(data)
    archive.writestr(item, data)


def write_file(archive: zipfile.ZipFile, name: str, path: Path, mode: int = 0o100644) -> None:
    item = info(name, mode)
    item.file_size = path.stat().st_size
    with path.open("rb") as source, archive.open(item, "w", force_zip64=False) as target:
        while block := source.read(COPY_SIZE):
            target.write(block)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rootfs", required=True, type=Path)
    parser.add_argument("--boot", required=True, type=Path)
    parser.add_argument("--installer", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    rootfs_size = args.rootfs.stat().st_size
    part_count = (rootfs_size + CHUNK_SIZE - 1) // CHUNK_SIZE
    if part_count > 100:
        raise SystemExit("Too many rootfs chunks for two-digit part names")

    part_names = [f"ubuntu.img.part{index:02d}" for index in range(part_count)]
    boot_sha = digest(args.boot)
    rootfs_sha = digest(args.rootfs)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(
        args.output,
        "w",
        compression=zipfile.ZIP_DEFLATED,
        compresslevel=9,
        allowZip64=False,
    ) as archive:
        write_file(
            archive,
            "META-INF/com/google/android/update-binary",
            args.installer / "update-binary",
            0o100755,
        )
        write_file(
            archive,
            "META-INF/com/google/android/updater-script",
            args.installer / "updater-script",
        )
        write_file(archive, "boot.img", args.boot)
        write_bytes(archive, "boot.img.sha256", f"{boot_sha}  boot.img\n".encode())
        write_bytes(archive, "ubuntu.img.sha256", f"{rootfs_sha}  ubuntu.img\n".encode())
        write_bytes(archive, "ubuntu.img.size-kb", f"{rootfs_size // 1024}\n".encode())
        write_bytes(archive, "ubuntu.img.parts", ("\n".join(part_names) + "\n").encode())

        with args.rootfs.open("rb") as source:
            for index, name in enumerate(part_names):
                remaining = min(CHUNK_SIZE, rootfs_size - index * CHUNK_SIZE)
                item = info(name)
                item.file_size = remaining
                with archive.open(item, "w", force_zip64=False) as target:
                    while remaining:
                        block = source.read(min(COPY_SIZE, remaining))
                        if not block:
                            raise EOFError(f"Unexpected end of {args.rootfs}")
                        target.write(block)
                        remaining -= len(block)

    print(args.output)
    print(f"sha256={digest(args.output)}")


if __name__ == "__main__":
    main()
