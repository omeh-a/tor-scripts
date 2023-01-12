# kernelmark
#   Tool to automatically build Linux kernels and deploy them over TFTP to PXE
#   Linux, targeting local build system @ TS.
# Matt Rossouw (omeh-a)
# 12/2022

import sys
import json
import os
from signal import signal, SIGINT, SIGKILL

import deploy
from finalise import finalise_iperf3
from machine import *
import build
from error import *
import test
from logfile import *

NUM_ARGS = 2    # mandatory arguments
MAX_FAILS = 8   # maximum number of consecutive build failures

tester_pid = 0

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

    # Register signal handler for interrupt
    signal(SIGINT, interrupt_handler)

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

    skipdone = False
    buildonly = False
    # Collect remaining flags
    for i in range(NUM_ARGS + 1, len(sys.argv)):
        if sys.argv[i] == "hardclean":
            build.nuke_output()
        elif sys.argv[i] == "clean":
            build.clean(m.name)
        elif sys.argv[i] == "skipdone":
            skipdone = True
        elif sys.argv[i] == "buildonly":
            buildonly = True
        else:
            print(f"Unknown flag: {sys.argv[i]} - continuing.")

    num_fails = 0  # consequetive build failures - if this exceeds MAX_FAILS, we stop

    alert(f"kernelmark started. target: {machine} kernels: {kernels_file}.")

    # Main loop
    for major in kernels:
        first_major = False  # DISABLED - Need to make clean to get new kernel headers
        for kernel in kernels[major]:
            alert(f"\033[01m ### STARTING TEST: kernel {kernel} ###\033[00m")
            if (num_fails >= MAX_FAILS):
                alert(f"Too many consecutive build failures! Last unsuccessful build was v {kernel}. \
                    {successful_builds} successful out of {successful_builds + failed_builds} builds.")
                exit()

            status = build.build(m, kernel, first_major)

            if status == ERR_OK:
                alert(f"Kernel version {kernel} built successfully.")
                successful_builds += 1
                num_fails = 0
            else:
                sub_status = ERR_OK
                if not first_major:
                    alert(
                        f"Kernel version {kernel} failed to build. Retrying with make clean.")
                    sub_status = build.build(m, kernel, True)
                if sub_status != ERR_OK:
                    alert(
                        f"Kernel version {kernel} failed to build. Continuing")
                    num_fails += 1
                    failed_builds += 1
                    continue

            first_major = False

            if buildonly:
                alert("Not testing because buildonly enabled!")
                continue

            if skipdone and build.kernel_built(m, kernel) and test.tests_exist(m, kernel):
                alert(
                    f"Skipping test on kernel {kernel} because it is already built and a test has run.")
                continue

            # Summon test process first, since we want to keep the status of the deployment
            # in the parent thread (because failing to deploy is a fatal error and should stop us)
            tester_pid = test.test(m, kernel)
            status = deploy.deploy(m, kernel)
            if status:
                print_err(status)
                os.kill(tester_pid, SIGKILL)
                exit()

    os.system(f"mq.sh sem -signal {machine}")
    # if not buildonly:
    #     finalise_iperf3("../output", machine)
    alert(
        f"Kernel testing complete! {successful_builds} successful out of {successful_builds + failed_builds} builds.")


def alert(s):
    print("\033[91m {}\033[00m" .format(s))
    Logfile.log(f"ALERT: {s}\n")


def interrupt_handler(signal_received, frame):
    """
    Handle ctrl+C
    """
    alert("SIGINT received. Exiting")
    # os.system(f"mq.sh sem -signal {machine.name}")
    exit()


if __name__ == "__main__":
    main()
