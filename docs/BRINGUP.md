# Bring-up gates

## Gate 0 — identify and recover

1. Confirm Download Mode reports an Exynos `dream2lte` model.
2. Record the exact model, bootloader/baseband versions and active slot layout.
3. Back up EFS and keep the matching stock Odin firmware offline.
4. Confirm OEM unlocking and a working custom recovery.

Stop if the model is Snapdragon or OEM unlock is unavailable.

## Gate 1 — kernel artifact

- [x] `Image` and all selected DTBs build from the pinned sources.
- [x] Core Halium kernel config invariants are verified.
- [x] DTBH and header-v0 boot image packaging complete with pinned inputs.
- [ ] Confirm the result on the exact phone and bootloader revision.

## Gate 2 — diagnostic boot

- Package the Samsung DT image with the device tree's `dtbhtoolExynos` flow.
- Build `halium-boot` with the verified boot parameters.
- Prefer a recovery/temporary test path before writing boot storage; Samsung's
  bootloader may not expose a true temporary-boot command.
- Capture `dmesg`, last-kmsg/pstore and USB enumeration.

Pass condition: a stable diagnostic shell over USB networking.

Do not start this gate until the model number, bootloader version, recovery and
EFS backup have been recorded. The current artifacts are Exynos-only.

## Gate 3 — Ubuntu Touch rootfs

- Boot a matching Ubuntu Touch rootfs/system image.
- Validate display/touch, storage, charging, suspend and thermal behaviour.
- Then validate Wi-Fi/Bluetooth, audio, sensors, camera and GNSS.
- Modem calls, SMS and mobile data come last; do not test emergency calling.

## Later-tree backports

Import fixes from newer Android trees one subsystem at a time, retaining the
Halium 11 ABI. Each backport needs a separate commit and regression record.
Priorities are display/HWC, Wi-Fi, vibrator/home button, dual SIM, then modem.
