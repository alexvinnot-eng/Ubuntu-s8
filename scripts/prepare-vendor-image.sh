#!/bin/sh
set -eu

project_dir=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
. "$project_dir/sources.lock"

download_dir=${DOWNLOAD_DIR:-"$project_dir/out/downloads"}
work_dir=${VENDOR_WORK_DIR:-"$project_dir/out/vendor-work"}
rom=${LINEAGE_ROM:-"$download_dir/lineage-18.1-dream2lte.zip"}
output=${VENDOR_IMAGE:-"$project_dir/out/vendor.img"}
brotli=${BROTLI:-brotli}
mksquashfs=${MKSQUASHFS:-mksquashfs}
sdat2img_dir=${SDAT2IMG_DIR:-"$project_dir/work/sdat2img"}

for command in curl unzip debugfs find git python3 sha256sum wc "$brotli" "$mksquashfs"; do
    command -v "$command" >/dev/null 2>&1 || {
        printf 'Required command not found: %s\n' "$command" >&2
        exit 2
    }
done

mkdir -p "$download_dir" "$work_dir" "$(dirname -- "$output")"
if [ ! -f "$rom" ] || ! printf '%s  %s\n' "$LINEAGE_ROM_SHA256" "$rom" | sha256sum -c - >/dev/null 2>&1; then
    curl -fL --retry 3 --continue-at - -o "$rom" "$LINEAGE_ROM_URL"
fi
printf '%s  %s\n' "$LINEAGE_ROM_SHA256" "$rom" | sha256sum -c - >/dev/null
[ "$(wc -c < "$rom")" -eq "$LINEAGE_ROM_SIZE" ]

if [ ! -d "$sdat2img_dir/.git" ]; then
    mkdir -p "$(dirname -- "$sdat2img_dir")"
    git clone --filter=blob:none --no-checkout "$SDAT2IMG_URL" "$sdat2img_dir"
fi
git -C "$sdat2img_dir" fetch --depth=1 origin "$SDAT2IMG_COMMIT"
git -C "$sdat2img_dir" checkout --detach "$SDAT2IMG_COMMIT"

transfer="$work_dir/system.transfer.list"
new_dat="$work_dir/system.new.dat"
system_img="$work_dir/system.img"
extract_dir="$work_dir/vendor-root"
extract_marker="$work_dir/vendor-extract.complete"
pseudo_file="$work_dir/vendor.pseudo"

[ -s "$transfer" ] || unzip -p "$rom" system.transfer.list > "$transfer"
if [ ! -s "$new_dat" ]; then
    unzip -p "$rom" system.new.dat.br | "$brotli" -d -o "$new_dat"
fi
if [ ! -s "$system_img" ]; then
    python3 "$sdat2img_dir/sdat2img.py" "$transfer" "$new_dat" "$system_img"
fi

if [ ! -f "$extract_marker" ]; then
    mkdir -p "$extract_dir"
    debugfs -R "rdump /system/vendor $extract_dir" "$system_img" \
        2> "$work_dir/debugfs-rdump.log"
    test -f "$extract_dir/vendor/build.prop"
    test "$(find "$extract_dir/vendor" -type f | wc -l)" -ge 500
    printf '%s\n' complete > "$extract_marker"
fi
python3 "$project_dir/scripts/ext4-pseudo-metadata.py" \
    "$system_img" /system/vendor > "$pseudo_file"

"$mksquashfs" "$extract_dir/vendor" "$output" \
    -comp gzip -b 131072 -noappend -no-progress \
    -mkfs-time 0 -all-time 0 -root-uid 0 -root-gid 2000 \
    -pf "$pseudo_file" -pseudo-override

printf 'Vendor image built: %s\n' "$output"
sha256sum "$output"
