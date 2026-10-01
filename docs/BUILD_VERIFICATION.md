# Build verification

Verified on 2026-10-01 from the pinned kernel commit with the repository's
AppArmor-default config and patch set, using LineageOS AArch64 Android GCC 4.9.

Results: `make Image dtbs`, Samsung DTBH packaging, header-v0 boot packaging,
and LineageOS vendor extraction completed successfully.

| Artifact | Size | SHA-256 |
|---|---:|---|
| `Image` | 30,742,360 | `38fccd989e43b22128b6c544b1b70c8bab16788a1ba2de6e88b48b411174ebcc` |
| `exynos8895-dream2lte_eur_open_07.dtb` | 233,966 | `2b2c84b94a226cda5b728eb8fab0c5eb2c4e75db2cbd0fbb45d391e528152f0b` |
| `exynos8895-dream2lte_eur_open_08.dtb` | 233,899 | `d90b4adbaec7cc2e5f52be9ae3decf6174070de083eff82239717486d758ff2d` |
| `exynos8895-dream2lte_eur_open_09.dtb` | 233,493 | `b3a2d71f5495cd0b45eddb7b33da4cb968884a621e7a4cfcccb898c68f96c1b6` |
| `exynos8895-dream2lte_eur_open_10.dtb` | 233,534 | `5ac270a7972bf632ef91771fc53ab7305d0aeb442d4c27b113eca7d179ee8998` |
| `prebuilt_dt_dream2lte.img` | 944,128 | `0eeb51958dfd597a49ec36942a8c9daa6ee77f9c9dcd126f483ed87a6ca28d41` |
| `halium-boot-dream2lte.img` | 37,093,392 | `17afe1361c4dfb06bb770f0b0490b096929234fa442d60c993f80ddfe3565756` |
| `vendor-dream2lte.img` | 123,883,520 | `a8ffdb1a262b4c0b20265e9a9abd3b42c6bc60d2b92ea91d4a3bf53c94cc526f` |

`halium-boot-dream2lte.img` is 4,849,648 bytes below the 40 MiB partition
limit. `file(1)` recognizes it as an Android boot image with kernel address
`0x10008000`, ramdisk address `0x11000000`, 2 KiB pages and the expected
`buildvariant=userdebug` command line. The image ends with the Samsung
`SEANDROIDENFORCE` marker.

`vendor-dream2lte.img` is SquashFS 4.0, gzip/zlib compressed with 128 KiB
blocks. It contains 759 inodes and preserves the source vendor tree's numeric
UID/GID and permission metadata through a generated pseudo-file.

The hashes record this verified build, not a promise that legacy GCC and every
host tool produce bit-identical output on every machine. This is not evidence
that the images are safe to flash or boot on every S8+ Exynos revision.
