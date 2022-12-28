# error
#   Error handling for kernelmark
# Matt Rossouw (omeh-a)
# 12/2022

import machine
import build

# Error codes
ERR_OK = 0
ERR_B_BUILDROOT_DIED = 1
ERR_B_KERNEL_BUILD_FAILED = 2

def print_err(err):
    if err == ERR_OK:
        return
    elif err == ERR_B_BUILDROOT_DIED:
        print("Buildroot died unexpectedly.")
    elif err == ERR_B_KERNEL_BUILD_FAILED:
        print("Kernel build failed. See build log.")
    else:
        print("Unknown error.")