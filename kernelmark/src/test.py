# test
#   Testing stage for kernelmark. Invokes tester-side scripts to run tests and collect
#   results from target.
# Matt Rossouw (omeh-a)
# 12/2022

import json
import os
import socket
import time
from build import out_dir
from error import *
from machine import Machine

MAX_RETRIES = 30

def test(machine, kernel_ver):
    # Fork process, returning main thread
    if __name__ != "__main__":
        pid = os.fork()
    else:
        pid = 0

    if pid == 0:
        # Child process
        # Start by waiting until the system is booted by trying to send
        # a UDP packet to port 1345 until it succeeds.
        print("Waiting for system to boot...")
        while True:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                sock.sendto(b"Emu", (machine.ip, 1345))
                break
            except socket.error:
                time.sleep(5)
                continue
        
        # Server is ready. Wait again to give iperf time to start
        time.sleep(3)
        
        # ipbench is cooked, so skip that part and just do iperf3 for now

        # Invoke iperf3
        # Bidirectional TCP traffic 1 Gbps
        f = logfile(machine, kernel_ver, "iperf3-bidir-tcp-1g")
        os.system(f"iperf3 -c {machine.ip} i 10 -t 30 -P 10 -b 100M --bidir --logfile {f}")
        
        # Sleep between calls because we need to spin up a fresh server between runs
        time.sleep(3)

        # Birectional UDP traffic 1 Gbps
        f = logfile(machine, kernel_ver, "iperf3-bidir-udp-1g")
        os.system(f"iperf3 -c {machine.ip} i 10 -t 30 -P 10 -b 100M --bidir --logfile {f}")
        time.sleep(3)

        # Bidirectional TCP traffic 100 Mbps
        f = logfile(machine, kernel_ver, "iperf3-bidir-tcp-100m")
        os.system(f"iperf3 -c {machine.ip} i 10 -t 10 -P 10 -b 100M --bidir --logfile {f}")
        time.sleep(3)

        # Bidirectional UDP traffic 100 Mbps
        f = logfile(machine, kernel_ver, "iperf3-bidir-udp-100m")
        os.system(f"iperf3 -c {machine.ip} i 10 -t 10 -P 10 -b 100M --bidir -u --logfile {f}")
        time.sleep(3)
        
        # Unidirectional TCP traffic 1 Gbps
        f = logfile(machine, kernel_ver, "iperf3-unidir-tcp-1g")
        os.system(f"iperf3 -c {machine.ip} i 10 -t 30 -P 10 -b 100M --logfile {f}")

        # Unidirectional UDP traffic 1 Gbps
        f = logfile(machine, kernel_ver, "iperf3-unidir-udp-1g")
        os.system(f"iperf3 -c {machine.ip} i 10 -t 30 -P 10 -b 100M -u --logfile {f}")

        print("Done testing. Exiting child process.")

        exit(0)
    else:
        # Parent process
        return pid

def logfile(machine, kernel_ver, title):
    if os.path.exists(f"{out_dir}/{machine.name}/{kernel_ver}/{title}.log"):
        os.remove(f"{out_dir}/{machine.name}/{kernel_ver}/{title}.log")
    os.system(f"echo \"{title}\" > {out_dir}/{machine.name}/{kernel_ver}/{title}.log")
    return f"{out_dir}/{machine.name}/{kernel_ver}/{title}.log"

# Test test for standalone testing of this test
if __name__ == "__main__":
    mf = json.load(open("../conf/machines.json"))
    m = Machine("haswell3", mf["haswell3"])
    test(m, "5.19.17")
    exit()
