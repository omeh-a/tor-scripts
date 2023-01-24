# test
#   Testing stage for kernelmark. Invokes tester-side scripts to run tests and collect
#   results from target.
# Matt Rossouw (omeh-a)
# 12/2022

import json
import os
import socket
import time
import signal
from build import out_dir
from error import *
from machine import Machine

MAX_RETRIES = 40
TARGET_BW = 1000  # in megabits / sec
IPERF_PORT1 = 5000

pkt_sizes = [
    # 1448,
    1024, 512, 256, 128, 90
]

MAX_PKT_SZ = 1448

bws = [
    1000,
    750,
    500,
    250,
    100,
    50
]

MAX_CPUS = 8


def test(machine, kernel_ver, local, test_args):
    if __name__ != "__main__":
        pid = os.fork()
    else:
        pid = 0

    if pid == 0:
        # Child process
        # Start by waiting until the system is booted by trying to send
        # a UDP packet to port 1345 until it succeeds.
        if __name__ != "__main__":
            print("Waiting for system to boot...")
            buff_sz = 1000
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.bind((str(socket.INADDR_ANY), 1345))
            sock.settimeout(10.0)
            retries = 0

            while True:
                if retries > MAX_RETRIES:
                    print(
                        f"Tester thread failed to connect to {machine.name} on kernel {kernel_ver}")
                    exit()
                try:
                    sock.sendto(b"Emu", (machine.ip, 1345))
                    out = sock.recvfrom(buff_sz)[0]
                    print(str(out))
                    if out != b'Emu':
                        print("Incorrect packet returned!")
                        time.sleep(5)
                        retries += 1
                        continue
                    else:
                        print("Server found")
                        break

                except socket.error as e:
                    # print(f"Failed! {e}")
                    retries += 1
                    time.sleep(5)
                    continue
            print("Server ready!")
            sock.close()

            # Server is ready. Wait again to give iperf time to start
            time.sleep(5)

        # ipbench is cooked, so skip that part and just do iperf3 for now

        # Invoke iperf3
        dirs = []
        if "bidir" in test_args:
            dirs.append("bidir")
        if "unidir" in test_args:
            dirs.append("unidir")

        # Run for each direction
        for d in dirs:
            bidir = (d == "bidir")
            if "iperf-bw" in test_args:
                for bw in bws:
                    # TCP 100% bw
                    iperf3_test_single(machine, kernel_ver, MAX_PKT_SZ, bw, False, local, bidir)

                    # UDP 100% bw
                    iperf3_test_single(machine, kernel_ver, MAX_PKT_SZ, bw, True, local, bidir)
                    
                    # TCP multicore
                    iperf3_test_multi(machine, kernel_ver, MAX_PKT_SZ, bw, False, machine.logical_cpus, bidir)

                    # UDP multicore
                    iperf3_test_multi(machine, kernel_ver, MAX_PKT_SZ, bw, True, machine.logical_cpus, bidir)

            if "iperf-pktsize" in test_args:
                for sz in pkt_sizes:
                    # TCP 100% bw
                    iperf3_test_single(machine, kernel_ver, sz, TARGET_BW, False, local, bidir)

                    # UDP 100% bw
                    iperf3_test_single(machine, kernel_ver, sz, TARGET_BW, True, local, bidir)
                        
                    # TCP multicore
                    iperf3_test_multi(machine, kernel_ver, sz, TARGET_BW, False, machine.logical_cpus, bidir)

                    # UDP multicore
                    iperf3_test_multi(machine, kernel_ver, sz, TARGET_BW, True, machine.logical_cpus, bidir)

        if "ipbench" in test_args:    
            # Invoke ipbench tests
            os.system(f"../../runbench/runbenchnocpu > {kernel_ver}-{machine.name}")
            os.system(f"../../runbench/stopbench")
            time.sleep(5)
            print(f"Done testing.")
            exit(0)
    return pid



def iperf3_test_single(machine, kernel_ver, pkt_size, bw, udp, local, bidir):
    """
    Run an iperf3 test in a one-one test - one client and one server both single threaded.
    NOTE: if not using this with the local flag, it will not work outside of the TS network.
    """
    time.sleep(5)
    print(f"Testing {machine.ip} - {pkt_size} bytes - {bw}")
    iperf_common = f"-c {machine.ip} -t 50 -J --connect-timeout 5000 -p 5000"
    if bidir:
        iperf_common += " --bidir"

    f = ""
    if local:
        if udp:
            f = logfile(machine, kernel_ver, f"iperf3-local-udp-{bw}m-{pkt_size}")
            os.system(f"iperf3 {iperf_common} -b {bw}M -u --logfile {f} --length {pkt_size}")
        else:
            f = logfile(machine, kernel_ver, f"iperf3-local-tcp-{bw}m-{pkt_size}")
            os.system(f"iperf3 {iperf_common} -b {bw}M --logfile {f} --set-mss {pkt_size}")
        print(f"Local test {f} done.")
    else:
        # for each of these: run command on vb01, scp logfile back
        p = "tcp"
        if udp:
            p = "udp"
        if bidir:
            p += ".bidir"
        
        os.system(f"on -h vb01.keg.cse.unsw.edu.au -c 'rm -f /tmp/iperf3-log && iperf3 {iperf_common} -b {bw}M -u --logfile /tmp/iperf3-log --length {pkt_size}' && \
            scp vb01.keg.cse.unsw.edu.au:/tmp/iperf3-log {out_dir}/{machine.name}/{kernel_ver}/iperf3-st-{p}-{bw}m-{pkt_size}.test")
        print(f"Test {pkt_size}-{bw}-udp complete.\n")
        
    time.sleep(3)

def iperf3_test_multi(machine, kernel_ver, pkt_size, bw, udp, num_cpus, bidir):
    """
    Run multicore tests on num_cpus.
    """
    time.sleep(5)  
    print(f"Multicore testing {machine.ip} - {pkt_size} bytes - {bw}")
    if num_cpus > MAX_CPUS:
        print(f"Tried to test with too many cores! Max={MAX_CPUS} Requested={num_cpus}.")
    
    iperf_common = f"-c {machine.ip} -t 50 -J --connect-timeout 5000 -b {int(bw/num_cpus)}M --length {pkt_size} --bidir"
    if udp:
        iperf_common += " -u"
    if bidir:
        iperf_common += " --bidir"
    
    # spin up testers 2..8
    for i in range(1, num_cpus + 1):
        os.system(f"on -h vb0{str(i+1)}.keg.cse.unsw.edu.au -c 'rm -f /tmp/mtlog && iperf3 {iperf_common} -p {str(5000 + i)} --logfile /tmp/mtlog' &")
    
    # tester 1
    os.system(f"on -h vb01.keg.cse.unsw.edu.au -c 'rm -f ~/iperf3/vb01/log && iperf3 {iperf_common} -p 5000 --logfile ~/iperf3/vb01/log'")

    # once tester 1 unblocks, we can collect results and move on. wait, just in case.
    time.sleep(5)

    for i in range(0, num_cpus):
        print(f"Getting info from vb0{str(i+1)}")
        p = "tcp"
        if udp:
            p = "udp"
        if bidir:
            p += ".bidir"
        
        os.system(f"scp vb0{str(i+1)}.keg.cse.unsw.edu.au:/tmp/mtlog {out_dir}/{machine.name}/{kernel_ver}/iperf3-mt{i}-{p}-{bw}m-{pkt_size}.test")
    return

def logfile(machine, kernel_ver, title):
    if os.path.exists(f"{out_dir}/{machine.name}/{kernel_ver}/{title}.test"):
        os.remove(f"{out_dir}/{machine.name}/{kernel_ver}/{title}.test")
    os.system(f"touch {out_dir}/{machine.name}/{kernel_ver}/{title}.test")
    return f"{out_dir}/{machine.name}/{kernel_ver}/{title}.test"

def tests_exist(machine, kernel_ver):
    if os.path.exists(f"{out_dir}/{machine.name}/{kernel_ver}/iperf3-st-tcp-1000m-512.test"):
        return True
    return False

# Test test for standalone testing of this test
if __name__ == "__main__":
    import sys
    from kernelmark import DEFAULT_TESTFLAGS
    if len(sys.argv) != 2:
        print("USAGE: test.py [machine]")
    mf = json.load(open("../conf/machines.json"))
    m = Machine(sys.argv[1], mf[sys.argv[1]])
    test(m, "debian_bullseye", False, DEFAULT_TESTFLAGS)
    exit()
