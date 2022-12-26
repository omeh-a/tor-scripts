# kernelmark
#   Tool to automatically build Linux kernels and deploy them over TFTP to PXE
#   Linux, targeting local build system @ TS.
# Matt Rossouw (omeh-a)
# 12/2022

import sys
import json
import os

NUM_ARGS = 1
def usage():
    print("USAGE: kernelmark [system]")
    exit()

def main():
    print("Starting.")

    # Collect commandline arguments
    if (len(sys.argv) < NUM_ARGS + 1):
        usage() 

    machine = sys.argv[1]

    # Check if an entry for this machine is in the manifest
    mf = json.load(os.read("../conf/machines.json"))
    

if __name__ == "__main__":
    main()