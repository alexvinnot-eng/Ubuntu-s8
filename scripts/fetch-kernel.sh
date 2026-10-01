#!/bin/sh
set -eu

project_dir=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
. "$project_dir/sources.lock"

kernel_dir=${KERNEL_DIR:-"$project_dir/work/kernel"}
mkdir -p "$(dirname -- "$kernel_dir")"

if [ ! -d "$kernel_dir/.git" ]; then
    git clone --filter=blob:none --branch "$KERNEL_BRANCH" "$KERNEL_URL" "$kernel_dir"
fi

git -C "$kernel_dir" fetch --depth=1 origin "$KERNEL_COMMIT"
git -C "$kernel_dir" checkout --detach "$KERNEL_COMMIT"

for patch_file in "$project_dir"/patches/kernel/*.patch; do
    if git -C "$kernel_dir" apply --check "$patch_file" 2>/dev/null; then
        git -C "$kernel_dir" apply "$patch_file"
    elif git -C "$kernel_dir" apply --reverse --check "$patch_file" 2>/dev/null; then
        printf 'Patch already applied: %s\n' "$(basename -- "$patch_file")"
    else
        printf 'Patch cannot be applied cleanly: %s\n' "$patch_file" >&2
        exit 1
    fi
done

printf 'Prepared kernel %s at %s\n' "$KERNEL_COMMIT" "$kernel_dir"
