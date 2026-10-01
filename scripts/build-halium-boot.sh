#!/bin/sh
set -eu

project_dir=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
. "$project_dir/sources.lock"
kernel=${KERNEL_IMAGE:-"$project_dir/out/kernel/arch/arm64/boot/Image"}
dt_image=${DT_IMAGE:-"$project_dir/prebuilt_dt_dream2lte.img"}
download_dir=${DOWNLOAD_DIR:-"$project_dir/out/downloads"}
output=${BOOT_IMAGE:-"$project_dir/out/halium-boot-dream2lte.img"}
partition_size=41943040
mkdir -p "$download_dir" "$(dirname -- "$output")"
initramfs="$download_dir/initrd.img-touch-arm64"
mkbootimg="$download_dir/mkbootimg.py"

fetch_checked() {
    url=$1; expected=$2; destination=$3
    if [ ! -f "$destination" ] || ! printf '%s  %s\n' "$expected" "$destination" | sha256sum -c - >/dev/null 2>&1; then
        curl -fL --retry 3 -o "$destination" "$url"
    fi
    printf '%s  %s\n' "$expected" "$destination" | sha256sum -c - >/dev/null
}
fetch_checked "$INITRAMFS_URL" "$INITRAMFS_SHA256" "$initramfs"
fetch_checked "$MKBOOTIMG_URL" "$MKBOOTIMG_SHA256" "$mkbootimg"
test -s "$kernel"; test -s "$dt_image"
python3 "$mkbootimg" --kernel "$kernel" --ramdisk "$initramfs" \
    --cmdline 'buildvariant=userdebug' --header_version 0 \
    --os_version 11 --os_patch_level 2022-06 --base 0x10000000 \
    --kernel_offset 0x00008000 --ramdisk_offset 0x01000000 \
    --second_offset 0x00f00000 --tags_offset 0x00000100 --pagesize 2048 \
    --dt "$dt_image" -o "$output"
printf 'SEANDROIDENFORCE' >> "$output"
size=$(wc -c < "$output")
[ "$size" -le "$partition_size" ] || { printf 'Boot image too large\n' >&2; exit 1; }
printf 'Halium boot image built: %s (%s bytes free)\n' "$output" "$((partition_size - size))"
