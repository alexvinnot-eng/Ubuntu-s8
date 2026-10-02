#!/usr/bin/env python3
"""Patch a newc Halium initramfs for recoverable early-boot diagnostics."""

from __future__ import annotations

import gzip
import stat
import sys
from dataclasses import dataclass


@dataclass
class Entry:
    name: bytes
    fields: list[int]
    data: bytes


def align4(value: int) -> int:
    return (value + 3) & ~3


def parse_newc(raw: bytes) -> list[Entry]:
    entries: list[Entry] = []
    pos = 0
    while pos + 110 <= len(raw):
        magic = raw[pos : pos + 6]
        if magic not in (b"070701", b"070702"):
            raise ValueError(f"invalid newc magic at offset {pos}: {magic!r}")
        fields = [int(raw[pos + 6 + i * 8 : pos + 14 + i * 8], 16) for i in range(13)]
        pos += 110
        size = fields[6]
        name_size = fields[11]
        name = raw[pos : pos + name_size - 1]
        pos = align4(pos + name_size)
        data = raw[pos : pos + size]
        pos = align4(pos + size)
        if name == b"TRAILER!!!":
            return entries
        entries.append(Entry(name, fields, data))
    raise ValueError("newc archive has no trailer")


def encode_entry(entry: Entry) -> bytes:
    fields = entry.fields.copy()
    fields[6] = len(entry.data)
    fields[11] = len(entry.name) + 1
    out = bytearray(b"070701" + b"".join(f"{value:08x}".encode() for value in fields))
    out.extend(entry.name + b"\0")
    out.extend(b"\0" * (align4(len(out)) - len(out)))
    out.extend(entry.data)
    out.extend(b"\0" * (align4(len(out)) - len(out)))
    return bytes(out)


def build_newc(entries: list[Entry]) -> bytes:
    out = bytearray()
    for entry in entries:
        out.extend(encode_entry(entry))
    trailer = [0, stat.S_IFREG, 0, 0, 1, 0, 0, 0, 0, 0, 0, 11, 0]
    out.extend(encode_entry(Entry(b"TRAILER!!!", trailer, b"")))
    out.extend(b"\0" * ((512 - len(out) % 512) % 512))
    return bytes(out)


def patch_telnet(script: bytes) -> bytes:
    text = script.decode()
    text = text.replace(
        "        mkdir $GADGET_DIR/g1/functions/rndis.usb0\n"
        "        mkdir $GADGET_DIR/g1/functions/rndis_bam.rndis\n",
        "        mkdir $GADGET_DIR/g1/functions/rndis.usb0\n",
    )
    text = text.replace(
        "        ln -s $GADGET_DIR/g1/functions/rndis.usb0 $GADGET_DIR/g1/configs/c.1\n"
        "        ln -s $GADGET_DIR/g1/functions/rndis_bam.rndis $GADGET_DIR/g1/configs/c.1\n",
        "        ln -s ../../functions/rndis.usb0 $GADGET_DIR/g1/configs/c.1/rndis.usb0\n",
    )
    text = text.replace(
        "        ln -s $GADGET_DIR/g1/functions/rndis.usb0 $GADGET_DIR/g1/configs/c.1\n",
        "        ln -s ../../functions/rndis.usb0 $GADGET_DIR/g1/configs/c.1/rndis.usb0\n",
    )
    marker = 'usb_setup "halium-initrd telnet 192.168.2.15"\n'
    logger = r'''save_debug_log() {
    mkdir -p /debug-cache
    CACHEDEV=
    for candidate in /dev/disk/by-partlabel/CACHE /dev/block/platform/11120000.ufs/by-name/CACHE /dev/block/sda21; do
        if [ -b "$candidate" ]; then CACHEDEV="$candidate"; break; fi
    done
    if [ -n "$CACHEDEV" ] && mount -t ext4 -o rw "$CACHEDEV" /debug-cache; then
        {
            echo "Halium initramfs diagnostic"
            echo "reason: $REASON"
            echo "cmdline: $(cat /proc/cmdline)"
            echo "interfaces:"
            /sbin/ifconfig -a
            echo "udc:"
            ls -la /sys/class/udc
            echo "dmesg:"
            dmesg
        } > /debug-cache/ut-initramfs-debug.txt 2>&1
        sync
        umount /debug-cache
    fi
}

save_debug_log
usb_setup "halium-initrd telnet 192.168.2.15"
'''
    if marker not in text:
        raise ValueError("USB setup marker not found in telnet panic script")
    text = text.replace(marker, logger, 1)
    old = '''# Unable to set up USB interface? Reboot.
if [ x$USB_IFACE = xnotfound ]; then
	usb_info "Halium initrd Debug: ERROR: could not setup USB as usb0 or rndis0"
	dmesg
	sleep 60 # plenty long enough to check usb on host
	reboot -f
fi
'''
    new = '''# Keep the failed boot alive and save evidence for TWRP collection.
if [ x$USB_IFACE = xnotfound ]; then
	usb_info "Halium initrd Debug: ERROR: could not setup USB as usb0 or rndis0"
	dmesg
	save_debug_log
	while :; do sleep 3600; done
fi
'''
    if old not in text:
        raise ValueError("USB failure branch not found in telnet panic script")
    return text.replace(old, new, 1).encode()


def main() -> int:
    if len(sys.argv) != 3:
        print(f"usage: {sys.argv[0]} INPUT_INITRD OUTPUT_INITRD", file=sys.stderr)
        return 2
    with gzip.open(sys.argv[1], "rb") as source:
        entries = parse_newc(source.read())
    target = next((entry for entry in entries if entry.name == b"scripts/panic/telnet"), None)
    if target is None:
        raise ValueError("scripts/panic/telnet is missing from initramfs")
    target.data = patch_telnet(target.data)
    raw = build_newc(entries)
    with open(sys.argv[2], "wb") as destination:
        with gzip.GzipFile(filename="", mode="wb", fileobj=destination, mtime=0) as compressed:
            compressed.write(raw)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
