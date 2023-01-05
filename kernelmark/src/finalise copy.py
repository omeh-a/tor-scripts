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
        # sub = []
        # Open each test
        results[kernel] = {"UDP" : {}, "TCP" : {}}
        for file in os.listdir(f"{out_dir}/{machine_name}/{kernel}"):
            # Skip kernel, rootfs, etc.
            if not ".test" in file or not "iperf3" in file:
                continue
            with open(f"{out_dir}/{machine_name}/{kernel}/{file}") as f:
                result = json.load(f)
                
                if len(result["intervals"]) == 0:
                    continue
                
                # add in extra details

                # packet size
                packet_size = file.split("-")[3].split(".")[0] # cursed line but it works

                result["packet_sz"] = packet_size
                # target bandwidth
                bw = file.split("-")[2]

                # protocol
                protocol = result["start"]["test_start"]["protocol"]

                try:
                    results[kernel][protocol][bw].append(result)
                except KeyError:
                    results[kernel][protocol][bw] = []
                
                # sub.append(result)

        # results[kernel] = sub.copy()
    
    iperf3_graphs_throughput(results)
    iperf3_graphs_latency(results)
    iperf3_graphs_cpu(results)


def iperf3_graphs_throughput(results):
    """
    Generates plots of throughput against packet size for UDP results
    """
    for kernel in results:
        for protocol in results[kernel]:
            for bw in results[kernel][protocol]:
                plt.clf()
                packet_sizes = []
                throughput = []

                for test in results[kernel][protocol][bw]:
                    print(test["packet_sz"])
                    packet_sizes.append(test["packet_sz"])
                    throughput.append(float(test["end"]["sum_sent"]["bits_per_second"]) / 10**6) # in megabits
                print(packet_sizes)
                packet_sizes.reverse()
                throughput.reverse()
                plt.xlabel("Packet sizes (bytes)")
                tt = unitise_plot(throughput, "Throughput")
                plt.yticks(ticks(tt, 10))
                # pkt_ticks(packet_sizes)
                plt.ticklabel_format(style='sci', axis='y', useOffset=False)
                plt.title(f"Throughput performance for kernel {kernel} - {protocol} targeting {bw}b/s")
                ax = plt.gca()
                ax.yaxis.set_major_formatter('{x:9<5.1f}')
                plt.plot(packet_sizes, tt, "bo", packet_sizes, tt, "k")
                plt.savefig(f"../results/{kernel}-{bw}-{protocol}-throughput.png")
                
def iperf3_graphs_latency(results):
    """
    Generates graphs of mean packet latency against packet size
    """
    for kernel in results:
        for protocol in results[kernel]:
            if protocol == "UDP":
                continue
            for bw in results[kernel][protocol]:
                plt.clf()
                packet_sizes = []
                latency = []

                for test in results[kernel][protocol][bw]:
                    packet_sizes.append(test["packet_sz"])
                    latency.append(test["end"]["streams"][0]["sender"]["mean_rtt"])
                packet_sizes.reverse()
                latency.reverse()
                plt.xlabel("Packet sizes (bytes)")
                plt.ylabel("Mean RTT latency (us)")
                plt.yticks(ticks(latency, 10))
                # pkt_ticks(packet_sizes)
                plt.ticklabel_format(style='sci', axis='y', useOffset=False)
                plt.title(f"TCP Latency for kernel {kernel} - targeting {bw}b/s")
                ax = plt.gca()
                ax.yaxis.set_major_formatter('{x:9<5.1f}')
                plt.plot(packet_sizes, latency, "bo", packet_sizes, latency, "k")
                plt.savefig(f"../results/{kernel}-{bw}-latency.png")

def iperf3_graphs_cpu(results):
    """
    Generates graphs of CPU usage on receiver side against packet size
    """
    for kernel in results:
        for protocol in results[kernel]:
            for bw in results[kernel][protocol]:
                plt.clf()
                packet_sizes = []
                cpu = []

                for test in results[kernel][protocol][bw]:
                    packet_sizes.append(test["packet_sz"])
                    cpu.append(test["end"]["cpu_utilization_percent"]["remote_total"])
                packet_sizes.reverse()
                cpu.reverse()
                plt.xlabel("Packet sizes (bytes)")
                plt.ylabel("CPU usage (%)")
                plt.yticks(ticks(cpu, 10))
                # pkt_ticks(packet_sizes)
                plt.ticklabel_format(style='sci', axis='y', useOffset=False)
                plt.title(f"CPU utilisation for kernel {kernel} - {protocol} targeting {bw}b/s")
                ax = plt.gca()
                ax.yaxis.set_major_formatter('{x:9<5.1f}')
                plt.plot(packet_sizes, cpu, "bo", packet_sizes, cpu, "k")
                plt.savefig(f"../results/{kernel}-{bw}-{protocol}-CPU.png")

def ticks(data, num_ticks):
    """
    Create graph ticks for a dataset
    """
    minimum = int(min(data))
    maximum = int(max(data)) + 1
    # If it's not possible to create integer ticks, do it the goofy way
    if (maximum - minimum) < num_ticks:
        return [min(data), max(data)]
    
    num_ticks = int((maximum - minimum)/10) 
    return range(minimum, maximum, num_ticks)

def unitise_plot(data, axis_title):
    """
    Set appropriate data unit on y axis of plot
    """
    # Select appropriate unit
    if max(data) > 10:
        plt.ylabel(f"{axis_title} (MBits/sec)")
    elif max(data) > 1:
        plt.ylabel(f"{axis_title} (KBits/sec)")
        for i in range(len(data)):
            data[i] *= 1000
    else:
        plt.ylabel(f"{axis_title} (Bits/sec)")
        for i in range(len(data)):
            data[i] *= 1000000
    return data

def pkt_ticks(pkt_sizes):
    ticks = []
    for p in pkt_sizes:
        ticks.append(int(p))
    plt.xticks(ticks)

# For testing
if __name__ == "__main__":
    finalise_iperf3("/home/mattr/tor-scripts/kernelmark/output", "haswell4")
