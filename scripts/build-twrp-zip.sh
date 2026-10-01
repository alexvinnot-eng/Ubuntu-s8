#!/bin/sh
set -eu

project_dir=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
boot_image=${BOOT_IMAGE:-"$project_dir/out/halium-boot-dream2lte.img"}
output=${TWRP_ZIP:-"$project_dir/out/ubuntu-touch-dream2lte-sm-g955f-twrp.zip"}
stage="$project_dir/out/twrp-package"

command -v zip >/dev/null 2>&1 || {
    printf 'zip is required\n' >&2
    exit 1
}
[ -s "$boot_image" ] || {
    printf 'Missing boot image: %s\n' "$boot_image" >&2
    exit 1
}

boot_size=$(wc -c < "$boot_image")
[ "$boot_size" -le 41943040 ] || {
    printf 'Boot image exceeds the 40 MiB BOOT partition\n' >&2
    exit 1
}

rm -rf "$stage"
mkdir -p "$stage/META-INF/com/google/android" "$(dirname -- "$output")"
cp "$project_dir/twrp/META-INF/com/google/android/update-binary" \
    "$stage/META-INF/com/google/android/update-binary"
cp "$project_dir/twrp/META-INF/com/google/android/updater-script" \
    "$stage/META-INF/com/google/android/updater-script"
cp "$boot_image" "$stage/boot.img"
(
    cd "$stage"
    sha256sum boot.img > boot.img.sha256
    chmod 0755 META-INF/com/google/android/update-binary
    chmod 0644 META-INF/com/google/android/updater-script boot.img boot.img.sha256
    find . -exec touch -d '@1704067200' {} +
    rm -f "$output"
    zip -X -9 -r "$output" META-INF boot.img boot.img.sha256 >/dev/null
)

printf 'TWRP package: %s\n' "$output"
sha256sum "$output"
