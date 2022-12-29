# kernelmark
#   Tool to automatically build Linux kernels and deploy them over TFTP to PXE
#   Linux, targeting local build system @ TS.
# Matt Rossouw (omeh-a)
# 12/2022

import sys
import json
import os

import deploy
from machine import *
import build
from error import *
import test

NUM_ARGS = 2    # mandatory arguments
MAX_FAILS = 3   # maximum number of consecutive build failures

def usage():
    print("USAGE: kernelmark [system] [kernels.json] [flags]")
    print(" FLAGS: \n   hardclean - nuke output directory\n   clean - clean output directory for this system")
    exit()

def main():
    successful_builds = 0
    failed_builds = 0

    if os.name != "posix":
        print("This tool is only supported on POSIX systems.")
        exit()

    # Collect commandline arguments
    if (len(sys.argv) < NUM_ARGS + 1):
        usage() 

    machine = sys.argv[1]

    # Check if an entry for this machine is in the manifest json file
    mf = json.load(open("../conf/machines.json"))

    # Look for machine in mf json
    if machine not in mf:
        print("Machine not found in manifest.")
        exit()
    
    # Create machine object
    m = Machine(machine, mf[machine])

    # Collect target kernels
    kernels_file = sys.argv[2]
    kernels = json.load(open(kernels_file))

    # Collect remaining flags
    for i in range (NUM_ARGS + 1, len(sys.argv)):
        if sys.argv[i] == "hardclean":
            build.nuke_output()
        elif sys.argv[i] == "clean":
            build.clean(m.name)
        else:
            print(f"Unknown flag: {sys.argv[i]} - continuing.")


    num_fails = 0 # consequetive build failures - if this exceeds MAX_FAILS, we stop

    # Main loop
    for major in kernels:
        for kernel in kernels[major]:
            if (num_fails >= MAX_FAILS):
                print("Too many consecutive build failures! Last unsuccessful build was v" + kernel + ".")
                exit()
            
            status = build.build(m, kernel)

            if status == ERR_OK:
                print(f"Kernel version {kernel} built successfully.")
                successful_builds += 1
                num_fails = 0
            else:
                print(f"Kernel version {kernel} failed to build. Continuing")
                num_fails += 1
                failed_builds +=1

            # Summon test process first, since we want to keep the status of the deployment
            # in the parent thread (because failing to deploy is a fatal error and should stop us)
            tester_pid = test.test(m, kernel)
            status = deploy.deploy(m, kernel)
            if status:
                print_err(status)
                os.kill(tester_pid)
                exit()

    print(f"Kernel testing complete! {successful_builds} successful out of {successful_builds + failed_builds} builds.")

if __name__ == "__main__":
    main()