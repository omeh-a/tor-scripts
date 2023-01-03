# build
#   Build stage for kernelmark. Invokes the build script for each kernel version.
# Matt Rossouw (omeh-a)
# 12/2022

import json
import shutil
import machine
import os
from error import *


def build(machine, kernel_ver):
    # Check if this kernel version has already been built
    if os.path.exists(f"{out_dir}/{machine.name}/{kernel_ver}") \
            and os.path.exists(f"{out_dir}/{machine.name}/{kernel_ver}/bzImage"):
        print(f"Kernel version {kernel_ver} already built for {machine.name}.")
        return 0
    else:
        # Create output directory
        if not os.path.exists(f"{out_dir}/{machine.name}"):
            os.mkdir(f"{out_dir}/{machine.name}/")
        # Create kernel version directory
        if not os.path.exists(f"{out_dir}/{machine.name}/{kernel_ver}"):
            os.mkdir(f"{out_dir}/{machine.name}/{kernel_ver}")

    # Load buildroot configuration
    if os.path.exists(f"{br_conf_dir}/{machine.name}/.config"):
        os.remove(f"{br_dir}/.config")
    os.system(f"cp {br_conf_dir}/{machine.name}.config {br_dir}/.config")

    print("No existing kernel build found for this version. Building.")
    # Invoke kernel build
    os.chdir(f"{br_dir}/")
#    os.system("make clean")
    if os.system(f"make"):
        os.chdir(script_dir)
        return ERR_B_BUILDROOT_DIED

    os.system(f"cp output/images/bzImage {out_dir}/{machine.name}/{kernel_ver}/")
    os.system(f"cp output/images/rootfs.cpio {out_dir}/{machine.name}/{kernel_ver}/")

    os.chdir(script_dir)
    return 0


def nuke_output():
    """
    Totally cleans the output directory, inclusive of ALL systems. Use with caution.
    """
    shutil.rmtree(f"{out_dir}/")
    os.mkdir(f"{out_dir}/")
    os.chmod(f"{out_dir}/", 0o777)


def clean(m):
    """
    Cleans the output directory for the current system, leaving everything else alone.
    """
    shutil.rmtree(f"{out_dir}/{m}/")


# Initialisation - load configuration files
conf = json.load(open("../conf/build.json"))
br_dir = conf["buildroot-dir"]
out_dir = conf["output-dir"]
br_conf_dir = conf["br-conf-dir"]

if not os.path.exists(out_dir):
    os.mkdir(f"{out_dir}/")
    os.chmod(f"{out_dir}/", 0o777)

# Store directory of this script
script_dir = os.path.dirname(os.path.realpath(__file__))
