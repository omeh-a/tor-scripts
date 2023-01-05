# finalise
#   Script to collect and collate test results, generate graphs.
# Matt Rossouw (omeh-a)
# 01/23

import matplotlib.pyplot as plt
import json
import os

def finalise_iperf3(out_dir, machine_name):
    results = {}
    
    # Find all tests
    for kernel in os.listdir(f"{out_dir}/{machine_name}"):
        sub = []
        # Open each test
        for file in os.listdir(f"{out_dir}/{machine_name}/{kernel}"):
            # Skip kernel, rootfs, etc.
            if not ".test" in file or not "iperf3" in file:
                continue
            with open(f"{out_dir}/{machine_name}/{kernel}/{file}") as f:
                result = json.load(f)
                # add in extra details

                # packet size
                packet_size = file.split("-")[3].split(".")[0] # cursed line but it works
                result["packet_sz"] = packet_size
                
                # udp/tcp
                
                sub.append(result)

        results[kernel] = sub.copy()
    
    iperf3_graphs_throughput_udp(results)
    

def iperf3_graphs_throughput_udp(results):
    """
    Generates plots of throughput against packet size for UDP results
    """
    for kernel in results:
        packet_sizes = []
        throughput = []
        for test in results[kernel]:
            if test["start"]["test_start"]["protocol"] != "UDP":
                continue
            packet_sizes.append(test["packet_sz"])
            throughput.append(float(test["end"]["sum_sent"]["bits_per_second"]) / 10**6) # in megabits
        packet_sizes.reverse()
        throughput.reverse()
        
        print(packet_sizes)
        print(throughput)
        plt.plot(packet_sizes, throughput)
        plt.xlabel("Packet sizes (bytes)")
        plt.ylabel("Throughput (MBits/sec)")
        plt.yticks(range(int(min(throughput)), int(max(throughput)+1), int(len(range(int(min(throughput)), int(max(throughput)+1))) / 10)))
        plt.title(f"Throughput performance for kernel {kernel}")
        plt.savefig(f"../results/{kernel}.png")

# def iperf3_graphs_latency(results):
#     """
#     Generates graphs of mean packet latency against packet size
#     """






# For testing
if __name__ == "__main__":
    finalise_iperf3("/home/mattr/tor-scripts/kernelmark/output", "haswell3")
