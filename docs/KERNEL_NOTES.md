# Kernel adaptation notes

Base: `exynos8895/android_kernel_samsung_universal8895`, LineageOS 18.1,
commit `8d79a2d98eeb0100f890121dd5893b5d2e0b8d9c`.

The initial config was generated from `exynos8895-dream2lte_defconfig` and
processed with Halium's `check-kernel-config` for the Halium 11 target. Two
checker choices need device-specific exceptions:

- `CONFIG_RT_GROUP_SCHED=y`: Samsung's scheduler code directly uses RT group
  scheduling structures and fails to compile when the option is disabled.
- `# CONFIG_SYN_COOKIES is not set`: this downstream IPv6 stack expects older
  request-socket members that are absent in the tree when syncookies are on.

AppArmor is built in and selected through `CONFIG_DEFAULT_SECURITY="apparmor"`.
SELinux remains compiled for Android compatibility, but is not the default LSM;
this matches Ubuntu Touch's userspace confinement model.

Source compatibility patch:

- removes the duplicate DTC `yylloc` definition rejected by modern host GCC;
- retains strict `-Werror`, except for cross-enum comparisons in legacy Samsung
  modem code;
- casts two known modem comparisons explicitly to document their intent;
- initializes the DisplayPort AUX training delay only after the sink value has
  been read, fixing a real uninitialized-value bug exposed by strict GCC.
- represents the DECON clock table as integers. Its destination fields are
  `unsigned long`, so the former decimal constants were truncated at runtime
  while also causing forbidden floating-point code generation in the kernel.

These changes are build-enablement only. They do not establish that the modem,
telephony or suspend paths work on Ubuntu Touch; those require hardware logs.
