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

MAX_RETRIES = 25
TARGET_BW = 1000 # in megabits / sec
IPERF_PORT1 = 5000

pkt_sizes = [
    # 1448, 1024, 
    512, 256, 128, 90, 76, 64
]
# pkt_sizes = [1024]
MAX_CPUS = 8

def test(machine, kernel_ver, local):
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
                    print(f"Tester thread failed to connect to {machine.name} on kernel {kernel_ver}")
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
        for sz in pkt_sizes:
            # TCP multicore
            iperf3_test_multi(machine, kernel_ver, sz, TARGET_BW, False, machine.logical_cpus)

            # # UDP multicore
            # iperf3_test_multi(machine, kernel_ver, sz, TARGET_BW, False, machine.logical_cpus)

            # # TCP 100% bw
            # iperf3_test_single(machine, kernel_ver, sz, TARGET_BW, False, local)

            # # UDP 100% bw
            # iperf3_test_single(machine, kernel_ver, sz, TARGET_BW, True, local)

            # # TCP 10% bw
            # iperf3_test_single(machine, kernel_ver, sz, int(TARGET_BW/10), False, local)

            # # UDP 10% bw
            # iperf3_test_single(machine, kernel_ver, sz, int(TARGET_BW/10), True, local)
        

        time.sleep(5)
        print(f"Done testing.")
        exit(0)
    return pid



def iperf3_test_single(machine, kernel_ver, pkt_size, bw, udp, local):
    """
    Run an iperf3 test in a one-one test - one client and one server both single threaded.
    NOTE: if not using this with the local flag, it will not work outside of the TS network.
    """

    iperf_common = f"-c {machine.ip} -t 30 -J --connect-timeout 5000"
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
        if udp:
            os.system(f"on -h vb01 -c 'rm -f ~/iperf3/log && touch ~/iperf3/log && iperf3 {iperf_common} -b {bw}M -u --logfile ~/iperf3/log --length {pkt_size}' && \
                scp vb01:~/iperf3/log {out_dir}/{machine.name}/{kernel_ver}/iperf3-st-udp-{bw}m-{pkt_size}.test")
            print(f"Test {pkt_size}-{bw}-udp complete.\n")
        else:
            os.system(f"on -h vb01 -c 'rm -f ~/iperf3/log && touch ~/iperf3/log && iperf3 {iperf_common} -b {bw}M --logfile ~/iperf3/log --set-mss {pkt_size}' && \
                scp vb01:~/iperf3/log {out_dir}/{machine.name}/{kernel_ver}/iperf3-st-tcp-{bw}m-{pkt_size}.test")
            print(f"Test {pkt_size}-{bw}-tcp complete.\n")
    time.sleep(3)

def iperf3_test_multi(machine, kernel_ver, pkt_size, bw, udp, num_cpus):
    """
    Run multicore tests on num_cpus.
    """
    if num_cpus > MAX_CPUS:
        print(f"Tried to test with too many cores! Max={MAX_CPUS} Requested={num_cpus}.")
    
    iperf_common = f"-c {machine.ip} -t 30 -J --connect-timeout 5000 -b {int(bw/num_cpus)}M --length {pkt_size} --logfile ~/iperf3/log"
    if udp:
        iperf_common += " -u"
    
    # spin up testers 2..8
    for i in range(1, num_cpus):
        os.system(f"on -h vb0{str(i+1)} -c 'iperf3 {iperf_common} -p {str(5000 + i)}'  &")
        print(f"on -h vb0{str(i+1)} -c 'iperf3 {iperf_common} -p {str(5000 + i)}' &")
    
    # tester 1
    os.system(f"on -h vb01 -c 'iperf3 {iperf_common} -p 5000'")

    # once tester 1 unblocks, we can collect results and move on. wait, just in case.
    time.sleep(3)

    for i in range(0, num_cpus):
        if udp:
            os.system(f"scp vb0{str(i+1)}:~/iperf3/log {out_dir}/{machine.name}/{kernel_ver}/iperf3-mt{i}-udp-{bw}m-{pkt_size}.test")
        else:
            os.system(f"scp vb0{str(i+1)}:~/iperf3/log {out_dir}/{machine.name}/{kernel_ver}/iperf3-mt{i}-tcp-{bw}m-{pkt_size}.test")
    return

def logfile(machine, kernel_ver, title):
    if os.path.exists(f"{out_dir}/{machine.name}/{kernel_ver}/{title}.test"):
        os.remove(f"{out_dir}/{machine.name}/{kernel_ver}/{title}.test")
    os.system(f"touch {out_dir}/{machine.name}/{kernel_ver}/{title}.test")
    return f"{out_dir}/{machine.name}/{kernel_ver}/{title}.test"

def tests_exist(machine, kernel_ver):
    if os.path.exists(f"{out_dir}/{machine.name}/{kernel_ver}/iperf3-*-udp-100m-64.test"):
        return True
    return False

# Test test for standalone testing of this test
if __name__ == "__main__":
    mf = json.load(open("../conf/machines.json"))
    m = Machine("haswell3", mf["haswell3"])
    test(m, "6.1.1", False)
    exit()
