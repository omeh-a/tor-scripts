# deploy
#   Deploy stage for kernelmark. Invokes mq.sh to deploy the
#   kernel to the target machine on a new thread.
# Matt Rossouw (omeh-a)
# 12/2022

import os
from build import out_dir
from error import *
# from machine import Machine

def deploy(machine, kernel_ver):
    # Invoke mq.sh. Set with 300 second timeout to handle contigency of kernel panic
    os.system(f"mq.sh sem -signal {machine.name}")

    # os.execl("/home/mattr/bin/mq.sh", "/home/mattr/bin/mq.sh", "run", "-c", "Ostritch", "-s", f"{machine.name}", "-L", "-d", "1200", "-f", f"{out_dir}/{machine.name}/{kernel_ver}/Image", "-f", f"{out_dir}/{machine.name}/{kernel_ver}/rootfs.cpio")
    result = os.system(f"mq.sh run -c \"Ostritch\" -s {machine.name} -L \
        -d 1200 -f {out_dir}/{machine.name}/{kernel_ver}/*Image \
            -f {out_dir}/{machine.name}/{kernel_ver}/rootfs.cpio")
    return result 
    

if __name__ == "__main__":
    import sys
    from machine import Machine
    import json
    if len(sys.argv) < 3:
        print("USAGE: deploy.py [machine] [kernel]")
        exit(0)
    mf = json.load(open("../conf/machines.json"))
    m = Machine(sys.argv[1], mf[sys.argv[1]])
    deploy(m, sys.argv[2])