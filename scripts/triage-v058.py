#!/usr/bin/env python3
"""Read-only offline triage of a Halium/TWRP log tarball or experimental ZIP.

Uses only Python stdlib. Never extracts tar entries, mounts images, or writes
device partitions. Output is a short index to direct the next investigation.
"""
import argparse
import hashlib
import io
import re
import sys
import tarfile
import zipfile
from pathlib import Path

MAX_MEMBER = 16 * 1024 * 1024
PATTERNS = [
    ("segfault", re.compile(r"SIGSEGV|segmentation fault|signal 11|fatal signal 11|backtrace|tombstone", re.I)),
    ("tls", re.compile(r"static TLS|PT_TLS|thread.local|tls allocation|dlopen", re.I)),
    ("mount", re.compile(r"Could not mount ubuntu.img|mount.*(failed|error)|EXT4-fs.*error|loop.*(fail|error)|I/O error", re.I)),
    ("graphics", re.compile(r"lomiri|unity8|mirserver|hwcomposer|compositor|surfaceflinger|libhybris", re.I)),
    ("system", re.compile(r"kernel panic|watchdog|lxc.*(fail|error)|run-init|permission denied", re.I)),
]
TEXT_EXT = (".txt", ".log", ".dmesg", ".kmsg", ".out", ".err", ".json")
def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()

def scan(name, data, context):
    lines = data.decode("utf-8", errors="replace").splitlines()
    hits = []
    for i, line in enumerate(lines):
        tags = [k for k, pat in PATTERNS if pat.search(line)]
        if tags:
            hits.append((i, tags))
    print(f"\n{name}: {len(lines)} lines, {len(hits)} matching lines")
    shown = set()
    for i, tags in hits[:80]:
        for j in range(max(0, i - context), min(len(lines), i + context + 1)):
            if j not in shown:
                print(f"  {j + 1:>7} {lines[j][:400]}")
                shown.add(j)
        if context:
            print("  ---")
    if len(hits) > 80:
        print(f"  ... {len(hits) - 80} more matches")

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path, help=".tar.gz log archive, .zip TWRP package or raw log")
    parser.add_argument("--context", type=int, default=1, choices=range(0, 6))
    parser.add_argument("--expected-sha256", help="abort on digest mismatch")
    args = parser.parse_args()
    if not args.path.is_file():
        parser.error("file does not exist")
    sha = digest(args.path)
    print("file:", args.path)
    print("size:", args.path.stat().st_size)
    print("sha256:", sha)
    if args.expected_sha256 and sha.lower() != args.expected_sha256.lower():
        print("ERROR: SHA-256 mismatch; do not use this artifact", file=sys.stderr)
        return 2
    if tarfile.is_tarfile(args.path):
        with tarfile.open(args.path, "r:*") as tf:
            for member in tf:
                print(f"member: {member.name} ({member.size} bytes)")
                if not member.isfile() or member.size > MAX_MEMBER:
                    continue
                name = member.name.lower()
                if not (name.endswith(TEXT_EXT) or "log" in name or "pstore" in name or "dmesg" in name):
                    continue
                f = tf.extractfile(member)
                if f:
                    scan(member.name, f.read(MAX_MEMBER + 1)[:MAX_MEMBER], args.context)
    elif zipfile.is_zipfile(args.path):
        with zipfile.ZipFile(args.path) as zf:
            for item in zf.infolist():
                print(f"member: {item.filename} ({item.file_size} bytes)")
                if item.is_dir() or item.file_size > MAX_MEMBER:
                    continue
                if item.filename.lower().endswith((".sh", ".txt", ".log", ".prop", ".rc")):
                    scan(item.filename, zf.read(item), args.context)
    else:
        if args.path.stat().st_size > MAX_MEMBER:
            parser.error("raw log too large: max 16 MiB")
        scan(args.path.name, args.path.read_bytes(), args.context)
    return 0

if __name__ == "__main__":
    sys.exit(main())
