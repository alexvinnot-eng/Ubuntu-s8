#!/bin/sh
set -eu

project_dir=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
config_file=${1:-"$project_dir/config/exynos8895-dream2lte_halium_defconfig"}

require_value() {
    expected=$1
    if ! grep -qxF "$expected" "$config_file"; then
        printf 'Missing required config: %s\n' "$expected" >&2
        exit 1
    fi
}

require_value 'CONFIG_DEVTMPFS=y'
require_value 'CONFIG_CGROUPS=y'
require_value 'CONFIG_NAMESPACES=y'
require_value 'CONFIG_NET_NS=y'
require_value 'CONFIG_VT=y'
require_value 'CONFIG_UNIX98_PTYS=y'
require_value 'CONFIG_RT_GROUP_SCHED=y'
require_value '# CONFIG_SYN_COOKIES is not set'
printf 'Core Halium config invariants verified: %s\n' "$config_file"

