# build
#   Build stage for kernelmark. Invokes the build script for each kernel version.
# Matt Rossouw (omeh-a)
# 12/2022

import json
import machine
import os
from error import *



def build(machine, kernel_ver):
    # Check if this kernel version has already been built
    if os.path.exists(f"{out_dir}/{machine.name}/{kernel_ver}") \
        and len(os.listdir(f"{out_dir}/{machine.name}/{kernel_ver}")) > 0:
        print(f"Kernel version {kernel_ver} already built for {machine.name}.")
        return 0
    # Create output directory
    if not os.path.exists(f"{out_dir}/{machine.name}"):
        os.mkdir(f"{out_dir}/{machine.name}/")
    os.mkdir(f"{out_dir}/{machine.name}/{kernel_ver}")
    
    # Load buildroot configuration
    os.remove(f"{br_dir}/.config")
    os.cp(f"{br_conf_dir}/{machine.name}.config", f"{br_dir}/.config")

    # Invoke kernel build
    os.chdir(f"{br_dir}/")
    os.system("make clean")
    if os.system("make"):
        os.chdir(script_dir)
        return ERR_B_BUILDROOT_DIED
    os.chdir(script_dir)
    return 0


def nuke_output():
    """
    Totally cleans the output directory, inclusive of ALL systems. Use with caution.
    """
    os.rmdir(f"{out_dir}/")

def clean(m):
    """
    Cleans the output directory for the current system, leaving everything else alone.
    """
    os.rmdir(f"{out_dir}/{m}/")


# Open configuration file
conf = json.load(open("../conf/build.json"))
br_dir = conf["buildroot-dir"]
out_dir = conf["output-dir"]
br_conf_dir = conf["br-conf-dir"]

if not os.path.exists(out_dir):
    os.mkdir(f"{out_dir}/")
    os.chmod(f"{out_dir}/", 0o777)

# Store directory of this script
script_dir = os.path.dirname(os.path.realpath(__file__))
