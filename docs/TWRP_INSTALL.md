# TWRP diagnostic boot package for SM-G955F

The generated ZIP installs only `halium-boot` to the `BOOT` partition. It does
not format data, touch EFS, replace recovery, or install an Ubuntu Touch rootfs.
It is intended for the first diagnostic boot milestone on the Exynos
Samsung Galaxy S8+ `SM-G955F`.

## Build

Build and validate `out/halium-boot-dream2lte.img`, then run:

```sh
sh ./scripts/build-twrp-zip.sh
```

The output is `out/ubuntu-touch-dream2lte-sm-g955f-twrp.zip` together with a
printed SHA-256 digest. The installer performs these checks before writing:

1. A device property or bootloader string must positively identify `G955F`.
2. A block device named `BOOT` must exist.
3. The embedded boot image must fit the 40 MiB partition.
4. Its SHA-256 must match when `sha256sum` is available in recovery.

## Before installing

1. Keep the matching stock Odin firmware available on another computer.
2. Back up EFS and Boot in TWRP, and copy both backups off the phone.
3. Record the bootloader and baseband versions.
4. Verify the ZIP digest on the computer and again after copying it to the
   phone.

Do not use the ZIP on `SM-G955FD` or any Snapdragon S8+ model. If recovery
cannot positively identify `SM-G955F`, the installer exits before writing.

After installation, do not erase Android partitions. Reboot once and collect
USB enumeration, `dmesg`, pstore/last-kmsg, and recovery logs if the diagnostic
image does not reach a shell. Restore the Boot backup from TWRP to return to
the previous kernel and ramdisk.
