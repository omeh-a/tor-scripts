# finalise
#   Script to collect and collate test results, generate graphs.
# Matt Rossouw (omeh-a)
# 01/23

import matplotlib.pyplot as plt
import json
import os

IDEAL_LATENCY = 0.005

def finalise_iperf3(out_dir, machine_name):
    results = {}
    
    # Find all tests
    for kernel in os.listdir(f"{out_dir}/{machine_name}"):
        # sub = []
        # Open each test
        results[kernel] = {"UDP" : {}, "TCP" : {}}
        files = []
        for f in os.listdir(f"{out_dir}/{machine_name}/{kernel}"):
            if "iperf3" in str(f):
                files.append(f)

        files.sort(key=lambda filename: iperf3_filesort(filename))
            
        for file in files:
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
                    packet_sizes.append(test["packet_sz"])
                    throughput.append(float(test["end"]["sum_sent"]["bits_per_second"]) / 10**6) # in megabits
                plt.xlabel("Packet sizes (bytes)")
                tt = unitise_plot(throughput, "Throughput")
                #pkt_ticks(packet_sizes)
                plt.yticks(ticks(tt, 10))
                plt.ticklabel_format(style='plain', axis='y', useOffset=False)
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
                plt.xlabel("Packet sizes (bytes)")
                plt.ylabel("Mean RTT latency (us)")
                #pkt_ticks(packet_sizes)
                plt.yticks(ticks(latency, 10))
                plt.ticklabel_format(style='plain', axis='y', useOffset=False)
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
                plt.xlabel("Packet sizes (bytes)")
                plt.ylabel("CPU usage (%)")
                #pkt_ticks(packet_sizes)
                plt.yticks(ticks(cpu, 10))
                plt.ticklabel_format(style='plain', axis='y', useOffset=False)
                plt.title(f"CPU utilisation for kernel {kernel} - {protocol} targeting {bw}b/s")
                ax = plt.gca()
                ax.yaxis.set_major_formatter('{x:9<5.1f}')
                plt.plot(packet_sizes, cpu, "bo", packet_sizes, cpu, "k")
                plt.savefig(f"../results/{kernel}-{bw}-{protocol}-CPU.png")

def ticks(data, num_ticks):
    """((float(p) * 8) / IDEAL_LATENCY) / 1000or a dataset
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

def calculate_expected_throughput(pkt_sizes, bw):
    speeds = []
    for p in pkt_sizes:
        speeds.append(float(p) / (IDEAL_LATENCY))
    return speeds

def pkt_ticks(pkt_sizes):
    ticks = []
    for p in pkt_sizes:
        ticks.append(int(p))
    plt.xticks(ticks, pkt_sizes)
    

def iperf3_filesort(file):
    return int(file.split("-")[3].split(".")[0])


class iperf_results():
    def __init__(self, results):
        self.results = results
        pkt_sizes_udp = []
        pkt_sizes_tcp = []

        # Check packet sizes in the first test for both UDP and TCP
        for kernel in results:
            for bw in results[kernel]["udp"]:
                for test in results[kernel]["udp"][bw]:
                    pkt_sizes_udp.append(test["packet_sz"])
                for test in results[kernel]["tcp"][bw]:
                    pkt_sizes_tcp.append(test["packet_sz"])
                break
            break
        # hacky but whatever
        self.sizes_udp = pkt_sizes_udp
        self.sizes_tcp = pkt_sizes_tcp
    
    def get_result(self, bw, udp, kernel):
        throughput = []
        latency = []
        cpu = []
        
        if not udp:
            for test in self.results[kernel]["udp"][bw]:
                throughput.append(float(test["end"]["sum_sent"]["bits_per_second"]) / 10**6)
                latency.append(test["end"]["streams"][0]["sender"]["mean_rtt"])
                cpu.append(test["end"]["cpu_utilization_percent"]["remote_total"])

            return {"throughput" : throughput, "latency" : latency, "cpu" : cpu}
        else:
            for test in self.results[kernel]["udp"][bw]:
                throughput.append(float(test["end"]["sum_sent"]["bits_per_second"]) / 10**6)
                cpu.append(test["end"]["cpu_utilization_percent"]["remote_total"])

            return {"throughput" : throughput, "cpu" : cpu}
    
    def get_result_udp(self, bw, kernel):
        return self.get_result(bw, True, kernel)

    def get_result_tcp(self, bw, kernel):
        return self.get_result(self, bw, False, kernel)

    # def mean_throughput_by_major(self, bw, udp):
    #     # Get best performing throughput for each major version
        

# For testingg
if __name__ == "__main__":
    finalise_iperf3("/home/mattr/tor-scripts/kernelmark/output", "haswell3")
