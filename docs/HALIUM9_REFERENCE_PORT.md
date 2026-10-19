# Reference port: Halium 9 / Galaxy S8 (dreamlte), 2022

**Reference only; do not flash dreamlte artifacts on dream2lte.**

Jo-Blade reported Lomiri UI boot on the Galaxy S8 with Halium 9 in Halium/projectmanagement#262 and documented a follow-up in #292. The corresponding manifest is visible in Halium/halium-devices PR #331:

- https://github.com/Halium/projectmanagement/issues/262
- https://github.com/Halium/projectmanagement/issues/292
- https://github.com/Halium/halium-devices/pull/331/files

The 34-line manifest in PR #331 specifies:

| Component | Source | Revision |
|---|---|---|
| common device | abkro/android_device_samsung_universal8895-common | halium-9.0 |
| dreamlte device | abkro/android_device_samsung_dreamlte | halium-9.0 |
| universal8895 kernel | abkro/android_kernel_samsung_universal8895-1 | halium-9.0 |
| common vendor | exynos8895/android_vendor_samsung_universal8895-common | lineage-16.0 |
| dreamlte vendor | exynos8895/android_vendor_samsung_dreamlte | lineage-16.0 |
| hardware samsung | LineageOS/android_hardware_samsung | lineage-16.0 |
| device settings | LineageOS/android_packages_resources_devicesettings | lineage-16.0 |

Important: upstream uses **dreamlte (S8)**, while our target is **dream2lte (S8+)**. A working S8 manifest is a comparison reference, *not* a drop-in manifest. Changes to the device target, DTB/DTBO, partition layout, boot header or vendor image require independent validation.

## Targeted comparison instead of speculative rebuilds

1. Compare exact historical source revisions and modifications against our Halium 9 device/common/kernel/vendor trees.
2. Check Android display stack compatibility before changing q.so TLS again: Android 9 vendor EGL/HWC, libhybris ABI, linker namespace, and Qt/Mir module load order.
3. Review USB networking independently from compositor. #292 notes that its author needed a `usb-tethering` executable in rootfs `/usr/bin`, executable mode 0755. Do not fetch arbitrary binaries or install one until provenance and compatibility are verified.
4. Establish a single failure signature from v0.5.8 backtrace, then produce a focused v0.5.9 patch with one causal change.

This record is based on upstream public evidence as of 2026-10-19 and does not validate the current experimental image.
