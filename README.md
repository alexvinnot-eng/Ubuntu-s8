# Ubuntu Touch bring-up for Samsung Galaxy S8+ Exynos

Reproducible first-stage porting workspace for `dream2lte`, based on Halium 11
and the LineageOS 18.1 device/kernel trees.

## Scope and safety

Supported target: Samsung Galaxy S8+ Exynos (`dream2lte`), primarily SM-G955F
and SM-G955FD. **Do not use this on Snapdragon models** such as SM-G955U,
SM-G955U1, SM-G955W or SM-G9550.

This repository is a bring-up project, not a released ROM. The kernel build is
validated by CI/local compilation, but a boot image must not be flashed until
its ramdisk, DT image, partition layout and exact phone variant are verified.
Keep a current EFS backup and a known-good Odin package before device testing.

## Why Halium 11

LineageOS 18.1 is the newest well-defined Android base for the existing
`dream2lte` device family that maps directly to Halium 11. It is a smaller and
more diagnosable first-boot target than starting from an Android 16 tree.
Useful fixes from later Android trees can be backported after the first boot,
especially display/HWC, Wi-Fi, vibrator, dual-SIM and modem changes.

## Verified status

- Source revisions are pinned in `sources.lock`.
- The Samsung 4.9 kernel config has been adapted to Halium requirements.
- Host-tool DTC and GCC enum comparison build failures are patched.
- AppArmor is enabled and selected as the default Linux security module.
- Kernel `Image` and four `dream2lte` DTBs compile successfully; hashes are in
  `docs/BUILD_VERIFICATION.md`.
- A Samsung DTBH image and an Android-header-v0 `halium-boot` diagnostic image
  are built and structurally checked.
- A deterministic `vendor.img` can be produced from the pinned LineageOS 18.1
  package while retaining the ext4 UID/GID and mode metadata.
- Hardware logs from SM-G955F confirm that the Lineage kernel, DT and Halium
  initramfs boot and mount userdata successfully.
- The original v0.2.0 installer exposed a signed 32-bit size overflow in the
  TWRP unzip implementation before anything was flashed. The chunked v0.2.1
  installer and its compatibility fix are documented in `docs/V0.2.1.md`.
- No build is declared safe for daily use yet.

## Kernel build

Requirements: Linux, Git, GNU make, curl, bc, and an AArch64 Android GCC 4.9
toolchain. The LineageOS `android_prebuilts_gcc_linux-x86_aarch64_aarch64-linux-android-4.9`
toolchain is known to work.

```sh
export CROSS_COMPILE=/absolute/path/to/aarch64-linux-android-
./scripts/fetch-kernel.sh
./scripts/build-kernel.sh
```

Outputs are placed in `out/kernel/arch/arm64/boot/`. The build script refuses
to proceed if the pinned source commit does not match.

## DTBH and diagnostic boot image

After the kernel build:

```sh
./scripts/build-dt-image.sh
cp out/prebuilt_dt_dream2lte.img prebuilt_dt_dream2lte.img
./scripts/build-halium-boot.sh
```

The resulting `out/halium-boot-dream2lte.img` fits the 40 MiB boot partition
declared by the device tree. It is a bring-up image, not a completed Ubuntu
Touch installer.

## Vendor image from LineageOS 18.1

Install `brotli`, `e2fsprogs` (for `debugfs`) and `squashfs-tools`, then run:

```sh
./scripts/prepare-vendor-image.sh
```

The script verifies the ROM SHA-256, converts its block OTA payload to ext4,
extracts `/system/vendor`, and writes `out/vendor.img` as deterministic
SquashFS. Later Android releases remain useful as narrowly selected patch
donors, but they are not substituted wholesale for the Halium 11 userspace.

## Full Halium tree

A complete Android/Halium checkout needs roughly 200–300 GB of free space and
substantially more RAM than this small workspace provides. On a suitable build
machine:

```sh
repo init -u https://github.com/Halium/android -b halium-11.0 --depth=1
mkdir -p .repo/local_manifests
cp manifests/dream2lte.xml .repo/local_manifests/
repo sync -c -j8
```

The next milestone is the first hardware boot of the v0.2.1 full-rootfs image,
followed by USB/ADB collection and Lomiri/HWC diagnosis on the exact Exynos
model.

## Layout

- `config/`: tested kernel configuration
- `patches/kernel/`: minimal source compatibility fixes
- `manifests/`: Halium local manifest seed
- `scripts/`: deterministic fetch, configure, verify and build workflow
- `docs/BRINGUP.md`: hardware testing sequence and acceptance gates
