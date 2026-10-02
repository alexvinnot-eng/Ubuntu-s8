#!/usr/bin/env python3
"""Patch the four embedded dream2lte DTBs without changing their size.

Samsung's DT bootargs use ``console=ram``.  The kernel has no ``ram``
console, so klibc run-init cannot open /dev/console and never hands off to
systemd.  ``console=tty`` is length-neutral and the Linux console parser
resolves it to the tty driver at index 0 (the same target as tty0).
"""

from pathlib import Path
import sys


if len(sys.argv) != 3:
    raise SystemExit(f"usage: {sys.argv[0]} INPUT_BOOT OUTPUT_BOOT")

source = Path(sys.argv[1])
target = Path(sys.argv[2])
before = b"console=ram"
after = b"console=tty"

data = source.read_bytes()
count = data.count(before)
if count != 4:
    raise SystemExit(f"expected 4 embedded DTB console strings, found {count}")
if data.count(after):
    raise SystemExit("output console string already exists in input")

patched = data.replace(before, after)
if len(patched) != len(data):
    raise SystemExit("length-neutral DTB patch unexpectedly changed boot image size")
if patched.count(after) != 4 or patched.count(before):
    raise SystemExit("DTB console replacement verification failed")

target.write_bytes(patched)
print(f"patched {count} DTBs: {source} -> {target}")
