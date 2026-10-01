#!/bin/sh
set -eu

project_dir=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
. "$project_dir/sources.lock"

kernel_dir=${KERNEL_DIR:-"$project_dir/work/kernel"}
out_dir=${OUT_DIR:-"$project_dir/out/kernel"}
jobs=${JOBS:-$(getconf _NPROCESSORS_ONLN 2>/dev/null || printf 4)}

if [ -z "${CROSS_COMPILE:-}" ]; then
    printf '%s\n' 'CROSS_COMPILE must point to an AArch64 Android GCC 4.9 prefix.' >&2
    exit 2
fi
if [ ! -x "${CROSS_COMPILE}gcc" ]; then
    printf 'Compiler not found: %sgcc\n' "$CROSS_COMPILE" >&2
    exit 2
fi
if [ "$(git -C "$kernel_dir" rev-parse HEAD)" != "$KERNEL_COMMIT" ]; then
    printf '%s\n' 'Kernel checkout is not at the pinned commit.' >&2
    exit 2
fi

mkdir -p "$out_dir"
config="$project_dir/config/exynos8895-dream2lte_halium_defconfig"
config_stamp="$out_dir/.dream2lte-config.sha256"
config_sha256=$(sha256sum "$config" | cut -d' ' -f1)
config_changed=false
if [ ! -f "$out_dir/.config" ] || [ ! -f "$config_stamp" ] || \
   [ "$(cat "$config_stamp")" != "$config_sha256" ]; then
    cp "$config" "$out_dir/.config"
    printf '%s\n' "$config_sha256" > "$config_stamp"
    config_changed=true
fi

export ARCH=arm64
export PLATFORM_VERSION=11.0.0
export KBUILD_BUILD_USER=${KBUILD_BUILD_USER:-ubports}
export KBUILD_BUILD_HOST=${KBUILD_BUILD_HOST:-dream2lte-builder}
export KBUILD_BUILD_TIMESTAMP=${KBUILD_BUILD_TIMESTAMP:-"Thu Jan  1 00:00:00 UTC 1970"}
export KBUILD_BUILD_VERSION=${KBUILD_BUILD_VERSION:-1}
if "$config_changed"; then
    make -C "$kernel_dir" O="$out_dir" olddefconfig
fi
make -C "$kernel_dir" O="$out_dir" -j"$jobs" Image dtbs

test -s "$out_dir/arch/arm64/boot/Image"
printf 'Kernel built: %s\n' "$out_dir/arch/arm64/boot/Image"
