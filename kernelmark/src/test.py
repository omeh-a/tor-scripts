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

MAX_RETRIES = 25
TARGET_BW = 1000 # in megabits / sec

pkt_sizes = [
    1448, 1024, 512, 256, 128
]

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
        time.sleep(3)
        
        # ipbench is cooked, so skip that part and just do iperf3 for now

        # Invoke iperf3
        for sz in pkt_sizes:
            # TCP 100% bw
            iperf3_test_single_local(machine, kernel_ver, sz, TARGET_BW, False)

            # UDP 100% bw
            iperf3_test_single_local(machine, kernel_ver, sz, TARGET_BW, True)

            # TCP 10% bw
            iperf3_test_single_local(machine, kernel_ver, sz, int(TARGET_BW/10), False)

            # UDP 10% bw
            iperf3_test_single_local(machine, kernel_ver, sz, int(TARGET_BW/10), True)
        

        # # Bidirectional TCP traffic 1 Gbps 10 threads
        # f = logfile(machine, kernel_ver, "iperf3-bidir-tcp-1g-10P")
        # os.system(f"iperf3 {iperf_common} -b 1000M -P 10--bidir --logfile {f}")
        
        # # Birectional UDP traffic 1 Gbps 10 threads
        # f = logfile(machine, kernel_ver, "iperf3-bidir-udp-1g-10P")
        # os.system(f"iperf3 {iperf_common} -b 1000M --bidir -u --logfile {f}")
        # time.sleep(3)

        # # Bidirectional TCP traffic 100 Mbps 100 threads
        # f = logfile(machine, kernel_ver, "iperf3-bidir-tcp-100m-100P")
        # os.system(f"iperf3 {iperf_common} -b 100M  -P 100 --bidir --logfile {f}")
        # time.sleep(3)

        # # Bidirectional UDP traffic 100 Mbps 100 threads
        # f = logfile(machine, kernel_ver, "iperf3-bidir-udp-100m-100P")
        # os.system(f"iperf3 {iperf_common} -b 100M -P 100 --bidir -u --logfile {f}")
        # time.sleep(3)
        
        # # Unidirectional TCP traffic 1 Gbps 1 thread
        # f = logfile(machine, kernel_ver, "iperf3-unidir-tcp-1g-1T")
        # os.system(f"iperf3 {iperf_common} -b 1000M --logfile {f}")

        # # Unidirectional UDP traffic 1 Gbps 1 thread
        # f = logfile(machine, kernel_ver, "iperf3-unidir-udp-1g-1T")
        # os.system(f"iperf3 {iperf_common} -b 1000M -u --logfile {f}")

        print("Done testing. Exiting child process.")

        exit(0)
    else:
        # Parent process
        return pid

def iperf3_test_single_local(machine, kernel_ver, pkt_size, bw, udp):
    """
    Run an iperf3 test in a one-one test - one client and one server both single threaded.
    NOTE: this function generates load LOCALLY - not using a remote system.
    """

    iperf_common = f"-c {machine.ip} i 10 -t 15 -J --connect-timeout 5000"
    f = ""
    if udp:
        f = logfile(machine, kernel_ver, f"iperf3-udp-{bw}m-{pkt_size}")
        os.system(f"iperf3 {iperf_common} -b {bw}M -u --logfile {f} --length {pkt_size}")
    else:
        f = logfile(machine, kernel_ver, f"iperf3-tcp-{bw}m-{pkt_size}")
        os.system(f"iperf3 {iperf_common} -b {bw}M --logfile {f} --set-mss {pkt_size}")
    
    print(f"Test {f} complete.\n")

    time.sleep(3)


def logfile(machine, kernel_ver, title):
    if os.path.exists(f"{out_dir}/{machine.name}/{kernel_ver}/{title}.test"):
        os.remove(f"{out_dir}/{machine.name}/{kernel_ver}/{title}.test")
    os.system(f"echo \"{title}\" > {out_dir}/{machine.name}/{kernel_ver}/{title}.log")
    return f"{out_dir}/{machine.name}/{kernel_ver}/{title}.test"

def tests_exist(machine, kernel_ver):
    if os.path.exists(f"{out_dir}/{machine.name}/{kernel_ver}/iperf3-unidir-udp-1g-1T.log"):
        return True
    return False

# Test test for standalone testing of this test
if __name__ == "__main__":
    mf = json.load(open("../conf/machines.json"))
    m = Machine("haswell3", mf["haswell3"])
    test(m, "5.19.17")
    exit()
