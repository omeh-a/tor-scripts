# build
#   Build stage for kernelmark. Invokes the build script for each kernel version.
# Matt Rossouw (omeh-a)
# 12/2022

import json
import shutil
import machine
import os
from error import *


def build(machine, kernel_ver, clean):
    # Check if this kernel version has already been built
    if kernel_built(machine, kernel_ver):
        print(f"Kernel version {kernel_ver} already built for {machine.name}.")
        return ERR_OK
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

    
    with open(".config", "a") as f:
        # Change kernel version
        f.write(f"BR2_LINUX_KERNEL_CUSTOM_VERSION_VALUE=\"{kernel_ver}\"\n")
        f.write(f"BR2_LINUX_KERNEL_VERSION=\"{kernel_ver}\"\n")

        # Set kernel headers
        write_kernel_headers(kernel_ver, f)

    if clean:
        os.system("make clean")
    if os.system(f"make > {out_dir}/{machine.name}/{kernel_ver}/build.log"):
        os.chdir(script_dir)
        return ERR_B_BUILDROOT_DIED

    os.system(f"cp output/images/*Image {out_dir}/{machine.name}/{kernel_ver}/Image")
    os.system(f"cp output/images/rootfs.cpio {out_dir}/{machine.name}/{kernel_ver}/rootfs.cpio")

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

def kernel_built(machine, kernel_ver):
    """
    Returns true if a build of the specified kernel is in the output directory.
    """
    if os.path.exists(f"{out_dir}/{machine.name}/{kernel_ver}") \
            and os.path.exists(f"{out_dir}/{machine.name}/{kernel_ver}/rootfs.cpio"):
        return True
    return False

def write_kernel_headers(kernel_ver, file):
    """
    Given a kernel version, write correct Buildroot parameter for kernel headers to file. Buildroot is a nightmare
    and this function documents that. You'd think changing the kernel version would be a "just change one thing" type 
    of affair but in reality you have to rewrite hundreds of lines of config.
    """
    print("Writing kernel headers...")
    vvv = kernel_ver.split(".")
    with open(f"{script_dir}/kernel_headers", 'r') as vers:
        for version in vers:
            # Don't copy version comment for target version
            if f"{vvv[0]}_{vvv[1]}" in version:
                continue
            
            # Otherwise, inject commented versions from versions file because
            # buildroot expects these for some reason.
            else:
                file.write(f"# {version[:len(version)-1]} is not set\n")

        # If version is later than 5.16, use 5.16 headers because they are the same
        if int(vvv[0]) > 5 and int(vvv[1]) >= 16:
            file.write("BR2_PACKAGE_HOST_LINUX_HEADERS_CUSTOM_5_16=y\n")
        
        # If version is earlier than 3, use very old 
        elif int(vvv[0]) < 3:
            file.write("BR2_PACKAGE_HOST_LINUX_HEADERS_CUSTOM_REALLY_OLD=y\n")

        # Otherwise, use exact version headers
        else:
            file.write(f"BR2_PACKAGE_HOST_LINUX_HEADERS_CUSTOM_{vvv[0]}_{vvv[1]}=y\n")
    
    file.write(f"BR2_DEFAULT_KERNEL_VERSION=\"{vvv[0]}.{vvv[1]}.{vvv[2]}\"\n")

    # Write at least tags
    with open(f"{script_dir}/kernel_headers_atleast", 'r') as headers:
        for h in headers:
            major = int(h[0])
            minor = int(h[2:len(h)-1])

            if int(vvv[0]) >= major and (int(vvv[1]) >= minor or int(vvv[0]) > major):
                file.write(f"BR2_TOOLCHAIN_HEADERS_AT_LEAST_{major}_{minor}=y\n")
            else:
                file.write(f"BR2_TOOLCHAIN_HEADERS_AT_LEAST_{major}_{minor}=n\n")
    
    # Write final at least
    if int(vvv[0]) >= 5 and (int(vvv[1]) >= 16 or int(vvv[0]) > 5):
        file.write("BR2_TOOLCHAIN_HEADERS_AT_LEAST=\"5.16\"\n")
        file.write(f"BR2_DEFAULT_KERNEL_HEADERS=\"5.16\"\n")
    else:
        file.write(f"BR2_TOOLCHAIN_HEADERS_AT_LEAST=\"{vvv[0]}.{vvv[1]}\"\n")
        file.write(f"BR2_DEFAULT_KERNEL_HEADERS=\"{vvv[0]}.{vvv[1]}\"\n")

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
