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
ERR_D_MQ_FAILED = 3

def print_err(err):
    if err == ERR_OK:
        return
    elif err == ERR_B_BUILDROOT_DIED:
        print("Buildroot died unexpectedly.")
    elif err == ERR_B_KERNEL_BUILD_FAILED:
        print("Kernel build failed. See build log.")
    elif err == ERR_D_MQ_FAILED:
        print("mq.sh failed to deploy kernel!")
    else:
        print("Unknown error.")