# defconfigs
This folder contains machine defconfigs to be used as a Linux kernel build config (not BuildRoot). To use these, move them to `/arch/[architecture]/configs/`. **don't need this for x86, or other standard platforms** - this is only for embedded systems which have weird configs.

## TELLING BUILDROOT TO USE THESE

Set parameter `BR2_LINUX_KERNEL_CUSTOM_CONFIG_FILE="[location]"`

## imx8mm

Use `imx_v8_defconfig`.
