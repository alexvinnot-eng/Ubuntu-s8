#!/usr/bin/env python3
"""Emit mksquashfs pseudo definitions for a directory inside an ext image."""

from __future__ import annotations

import os
import subprocess
import sys
from collections import deque


def fail(message: str) -> "NoReturn":
    print(message, file=sys.stderr)
    raise SystemExit(2)


if len(sys.argv) != 3:
    fail(f"usage: {sys.argv[0]} SYSTEM_IMAGE /path/in/image")

image = os.path.abspath(sys.argv[1])
source = sys.argv[2].rstrip("/") or "/"
if not os.path.isfile(image):
    fail(f"image not found: {image}")
if "\n" in source:
    fail("source path contains a newline")


def list_dir(path: str) -> list[tuple[int, int, int, str]]:
    result = subprocess.run(
        ["debugfs", "-R", f"ls -l -p {path}", image],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
    )
    entries = []
    for line in result.stdout.splitlines():
        if not line.startswith("/"):
            continue
        fields = line.split("/")
        if len(fields) < 7:
            continue
        mode_text, uid_text, gid_text, name = fields[2:6]
        if name in (".", ".."):
            continue
        if any(character.isspace() for character in name):
            fail(f"unsupported whitespace in ext4 entry name: {path}/{name}")
        entries.append((int(mode_text, 8), int(uid_text), int(gid_text), name))
    return entries


root_stat = subprocess.run(
    ["debugfs", "-R", f"stat {source}", image],
    check=True,
    text=True,
    stdout=subprocess.PIPE,
    stderr=subprocess.DEVNULL,
).stdout

import re

match = re.search(r"Mode:\s+([0-7]+).*?User:\s+(\d+)\s+Group:\s+(\d+)", root_stat, re.S)
if not match:
    fail(f"could not parse metadata for {source}")
root_mode, root_uid, root_gid = (int(match.group(1), 8), int(match.group(2)), int(match.group(3)))
print(f"/ d {root_mode & 0o7777:04o} {root_uid} {root_gid}")

queue: deque[tuple[str, str]] = deque([(source, "")])
while queue:
    ext_dir, relative_dir = queue.popleft()
    for mode, uid, gid, name in list_dir(ext_dir):
        relative = f"{relative_dir}/{name}".lstrip("/")
        print(f"{relative} m {mode & 0o7777:04o} {uid} {gid}")
        if mode & 0o170000 == 0o040000:
            queue.append((f"{ext_dir}/{name}", relative))
