# Halium 9 / LineageOS 16 experimental track (dream2lte)

Status date: 2026-10-19. Target: Samsung Galaxy S8+ Exynos SM-G955F (dream2lte).

**This is an unverified bring-up track, NOT a bootable release.** Keep the existing `main` branch as historical Halium 11 / LineageOS 18.1 work. Do not replace `sources.lock` or recycle its verified artifact checksums: those belong to the older track.

## Known reported experimental baseline (not independently reconstructed)

- Halium 9 / LineageOS 16.
- BOOT v0.4.6 unchanged in v0.5.6–v0.5.8 experiments.
- Vendor and Android/data not intentionally changed in those iterations.
- v0.5.6: q.so PT_TLS reportedly reduced 1568 -> 1056 bytes, exposing a 512-byte physical TLS store incorrectly accounted as 1024 bytes; compositor SIGSEGV.
- v0.5.7: bounded TLS store and compile-time capacity check; first TWRP flash sometimes fails with Error 1, "Could not mount ubuntu.img read-write", retry reported successful.
- v0.5.8: 1024-byte early TLS reservation/anchor, reported later q.so TLS burden 544 bytes, emergency backtrace added.
- Reported artifact name: `ut-v058-startup-tls-anchor-twrp.zip`.
- Reported SHA-256: `aa2d717d99da889ddcb8e512fbadbf12a2333f059f80962a81bcfaba1202465f`.
- TWRP collector: `sh /cache/ut-v058-collect.sh`; expected output `/data/media/0/ut-v058-logs.tar.gz`.

These values come from the test handoff, **not** an audited source tree or a locally verified archive. The original v0.5.8 ZIP, source patch and boot logs were not available in the accessible files at the time of writing. Do not imply a reproducible build or boot success.

## Highest-value next checks

1. Recover the original v0.5.8 log bundle; classify the earliest fatal event, identify PID/thread, module, signal address, mapped libraries, and stack symbol offsets.
2. Check whether compositor SIGSEGV happens **before or after** q.so is loaded. If before, stop trying to shrink q.so blindly.
3. Determine TLS *alignment*, module ID, ELF PT_TLS p_memsz/p_align, the loader's static TLS layout, actual store capacity and reservation lifetime. Distinguish load-time vs dlopen-time/static TLS constraints. An early 1024-byte reserve by itself does not prove correctness.
4. Inspect TWRP mount failure and distinguish low free space, ext4 corruption/dirty journal, loop device exhaustion, mount options and duplicate mounts. Do not add retries that conceal filesystem failure.
5. When boot is stable, independently test compositor/HWC and USB tethering. Historical Halium S8 port reported UI boot with USB networking needing a `usb-tethering` binary; **not evidence that this particular S8+ build boots**.

## Historical technical references

- Halium issue #262: https://github.com/Halium/projectmanagement/issues/262 (S8 Halium 9 collaboration and reports of display boot).
- Follow-up issue #292: https://github.com/Halium/projectmanagement/issues/292 (reported Halium 9 UI and USB-tethering requirement).
- These reports are for dreamlte (S8). Reuse for dream2lte (S8+) requires comparing device-specific DT/device settings and testing, never direct flash of another device's image.

## Safety

No wiping `/data`, Android/data, vendor, EFS, boot, or recovery as part of this documentation. Existing TWRP ZIP remains an experimental artifact. Preserve a known-good recovery path and backups before any future flash.

## Gate for a v0.5.9 build

Do not ship another TLS guess. Require: archived exact v0.5.8 binary/source inputs, inspected backtrace or ELF/TLS evidence, an explicit single-change hypothesis, static validation of artifact hashes, and a test rollback plan.
