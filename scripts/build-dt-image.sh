#!/bin/sh
set -eu

project_dir=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
. "$project_dir/sources.lock"

kernel_dir=${KERNEL_DIR:-"$project_dir/work/kernel"}
kernel_out=${KERNEL_OUT:-"$project_dir/out/kernel"}
hardware_dir=${HARDWARE_DIR:-"$project_dir/work/hardware-samsung"}
tool_dir=${TOOL_DIR:-"$project_dir/out/tools"}
dt_stage=${DT_STAGE:-"$project_dir/out/dream2lte-dtbs"}
output=${DT_IMAGE:-"$project_dir/out/prebuilt_dt_dream2lte.img"}

if [ ! -d "$hardware_dir/.git" ]; then
    mkdir -p "$(dirname -- "$hardware_dir")"
    git clone --filter=blob:none --no-checkout "$HARDWARE_SAMSUNG_URL" "$hardware_dir"
fi
git -C "$hardware_dir" fetch --depth=1 origin "$HARDWARE_SAMSUNG_COMMIT"
git -C "$hardware_dir" checkout --detach "$HARDWARE_SAMSUNG_COMMIT"

mkdir -p "$tool_dir" "$dt_stage" "$(dirname -- "$output")"
find "$dt_stage" -maxdepth 1 -type f -name '*.dtb' -delete
cp "$kernel_out"/arch/arm64/boot/dts/exynos/exynos8895-dream2lte_*.dtb "$dt_stage/"

cc -O2 \
    -I"$hardware_dir/dtbhtool/libdtbimg" \
    -I"$project_dir/vendor/include" \
    -I"$kernel_dir/scripts/dtc/libfdt" \
    "$hardware_dir/dtbhtool/mkdtbimg.c" \
    "$hardware_dir/dtbhtool/dtbimg.c" \
    "$kernel_dir/scripts/dtc/libfdt/fdt.c" \
    "$kernel_dir/scripts/dtc/libfdt/fdt_ro.c" \
    "$kernel_dir/scripts/dtc/libfdt/fdt_rw.c" \
    "$kernel_dir/scripts/dtc/libfdt/fdt_strerror.c" \
    "$kernel_dir/scripts/dtc/libfdt/fdt_sw.c" \
    "$kernel_dir/scripts/dtc/libfdt/fdt_wip.c" \
    "$kernel_dir/scripts/dtc/libfdt/fdt_empty_tree.c" \
    -o "$tool_dir/dtbhtoolExynos"

"$tool_dir/dtbhtoolExynos" -o "$output" -s 2048 \
    -p "$kernel_out/scripts/dtc/" "$dt_stage"
[ "$(dd if="$output" bs=1 count=4 2>/dev/null)" = "DTBH" ]
printf 'DT image built: %s\n' "$output"
