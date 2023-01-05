# deploy
#   Deploy stage for kernelmark. Invokes mq.sh to deploy the
#   kernel to the target machine on a new thread.
# Matt Rossouw (omeh-a)
# 12/2022

import os
from build import out_dir
from error import *
from machine import Machine

def deploy(machine, kernel_ver):
    # Invoke mq.sh. Set with 300 second timeout to handle contigency of kernel panic
    os.system(f"mq.sh sem -signal {machine.name}")
    result = os.system(f"mq.sh run -c \"Ostritch\" -s {machine.name} -L \
        -d 600 -f {out_dir}/{machine.name}/{kernel_ver}/bzImage \
            -f {out_dir}/{machine.name}/{kernel_ver}/rootfs.cpio")
    
    if result:
        return ERR_D_MQ_FAILED
    return 0
    
    