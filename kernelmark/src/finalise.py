# finalise
#   Script to collect and collate test results, generate graphs.
# Matt Rossouw (omeh-a)
# 01/23

import matplotlib.pyplot as plt
import json
import os
from statistics import mean

IDEAL_LATENCY = 0.005

def finalise_iperf3(out_dir, machine_name):
    results = {}
    
    # Find all tests
    for kernel in os.listdir(f"{out_dir}/{machine_name}"):
        # sub = []
        # Open each test
        results[kernel] = { "mt" : {"UDP" : {}, "TCP" : {}}, "st" : {"UDP" : {}, "TCP" : {}},}
        files = []
        for f in os.listdir(f"{out_dir}/{machine_name}/{kernel}"):
            if "iperf3" in str(f):
                files.append(f)

        files.sort(key=lambda filename: iperf3_filesort(filename))
        for file in files:
            # Skip kernel, rootfs, etc.
            if not ".test" in file or not "iperf3" in file:
                print(f"skipped {file}")
                continue
            with open(f"{out_dir}/{machine_name}/{kernel}/{file}") as f:
                try:
                    result = json.load(f)
                except:
                    print(f"Failed to open {machine_name} - {kernel} {file}")
                    continue

                if len(result["intervals"]) == 0:
                    continue
                
                # add in extra details
                # packet size
                packet_size = file.split("-")[4].split(".")[0] # cursed line but it works
                result["packet_sz"] = packet_size
                
                # target bandwidth
                bw = file.split("-")[3]

                # protocol
                protocol = result["start"]["test_start"]["protocol"]
                
                # for single threaded, don't do anything special
                if file.split("-")[1] == "st":
                    try:
                        results[kernel]["st"][protocol][bw].append(result)
                    except KeyError:
                        results[kernel]["st"][protocol][bw] = []
                # otherwise, for multithreaded we need to break this up further
                # yes i know this json stuff is a nightmare, but this saves having to reformat every single entry
                else:
                    # check this mt has an entry
                    try:
                        t = results[kernel]["mt"][protocol][file.split("-")[1]]
                    except KeyError:
                        
                        results[kernel]["mt"][protocol][file.split("-")[1]] = {}
                    try:
                        results[kernel]["mt"][protocol][file.split("-")[1]][bw].append(result)
                    except KeyError:
                        # try:
                        results[kernel]["mt"][protocol][file.split("-")[1]][bw] = []
                        # except KeyError:
                        results[kernel]["mt"][protocol][file.split("-")[1]][bw].append(result)
                            
    r = iperf_results(results, machine_name)
    iperf3_st_graphs_throughput(r)
    iperf3_st_graphs_latency(r)
    iperf3_st_graphs_cpu(r)
    iperf3_mt_graphs_throughput(r)
    iperf3_mt_graphs_cpu(r)
    iperf3_mt_graphs_latency(r)
    

def iperf3_st_graphs_throughput(results):
    """
    Generates plots of throughput against packet size for UDP/TCP results
    """
    for protocol in ["UDP", "TCP"]:
        for bw in results.bws:
            plt.clf()
            for kernel in results.kernels:
                # print(f"Graphing {protocol}-{bw}-{kernel}")
                sub = {}
                if protocol == "UDP":
                    sub = results.get_result_st_udp(bw, kernel)
                else:
                    sub = results.get_result_st_tcp(bw, kernel)
                if len(sub["throughput"]) == 0:
                    continue
                plt.xlabel("Packet sizes (bytes)")
                tt = unitise_plot(sub["throughput"], "Throughput")
                #pkt_ticks(packet_sizes)
                plt.yticks(ticks(tt, 10))
                # plt.ticklabel_format(style='plain', axis='y', useOffset=False)
                plt.title(f"Throughput performance - {protocol} targeting {bw[:len(bw)-1]}Mb/s")
                plt.plot(sub["packets"], tt, label=f"{kernel}")
            ax = plt.gca()
            ax.yaxis.set_major_formatter('{x:9<5.1f}')
            ax.legend()
            plt.savefig(f"../results/{results.machinename}-st-{bw}-{protocol}-throughput.png")

def iperf3_st_graphs_latency(results):
    """
    Generates plots of latency against packet size for TCP results
    """
    for protocol in ["TCP"]:
        for bw in results.bws:
            plt.clf()
            y_largest_range = []
            for kernel in results.kernels:
                # print(f"Graphing {protocol}-{bw}-{kernel}")
                sub = {}
                if protocol == "UDP":
                    packet_sizes = results.sizes_udp
                else:
                    sub = results.get_result_st_tcp(bw, kernel)
                if len(sub["latency"]) == 0:
                    continue
                
                if y_largest_range == [] or max(y_largest_range) < max(sub["latency"]):
                    y_largest_range = sub["latency"]

                plt.xlabel("Packet sizes (bytes)")
                # tt = unitise_plot(sub["latency"], "Latency")
                plt.ylabel("Latency (us)")
                #pkt_ticks(packet_sizes)
                # plt.ticklabel_format(style='plain', axis='y', useOffset=False)
                plt.title(f"Latency - {protocol} targeting {bw}b/s")
                plt.plot(sub["packets"], sub["latency"], label=f"{kernel}")
            plt.yticks(ticks(y_largest_range, 10))
            ax = plt.gca()
            ax.yaxis.set_major_formatter('{x:9<5.1f}')
            ax.legend()
            plt.savefig(f"../results/{results.machinename}-st-{bw}-{protocol}-latency.png")               

def iperf3_st_graphs_cpu(results):
    """
    Generates plots of cpu against packet size for UDP/TCP results
    """
    for protocol in ["TCP", "UDP"]:
        for bw in results.bws:
            plt.clf()
            y_range = []
            for kernel in results.kernels:
                # print(f"Graphing {protocol}-{bw}-{kernel}")
                sub = {}
                if protocol == "UDP":
                    sub = results.get_result_st_udp(bw, kernel)
                else:
                    sub = results.get_result_st_tcp(bw, kernel)
                if len(sub["cpu"]) == 0:
                    continue
                
                for cpu in sub["cpu"]:
                    if cpu not in y_range:
                        y_range.append(cpu)

                plt.xlabel("Packet sizes (bytes)")
                # tt = unitise_plot(sub["latency"], "Latency")
                plt.ylabel("CPU Utilisation (%)")
                #pkt_ticks(packet_sizes)
                # plt.ticklabel_format(style='plain', axis='y', useOffset=False)
                plt.title(f"CPU Utilisation - {protocol} targeting {bw[:len(bw)-1]}Mb/s")
                plt.plot(sub["packets"], sub["cpu"], label=f"{kernel}")
            plt.yticks(ticks(y_range, 10))
            ax = plt.gca()
            ax.yaxis.set_major_formatter('{x:9<5.1f}')
            ax.legend()
            plt.savefig(f"../results/{results.machinename}-st-{bw}-{protocol}-cpu.png")               

def iperf3_mt_graphs_throughput(results):
    """
    Generates plots of throughput against packet size for UDP/TCP results
    """
    for protocol in ["UDP", "TCP"]:
        for bw in results.bws:
            plt.clf()
            for kernel in results.kernels:
                # print(f"Graphing {protocol}-{bw}-{kernel}")
                sub = {}
                if protocol == "UDP":
                    sub = results.get_mt_result(bw, True, kernel)
                else:
                    sub = results.get_mt_result(bw, False, kernel)
                if len(sub["throughput"]) == 0:
                    continue
                plt.xlabel("Packet sizes (bytes)")
                tt = unitise_plot(sub["throughput"], "Throughput")
                #pkt_ticks(packet_sizes)
                plt.yticks(ticks(tt, 10))
                # plt.ticklabel_format(style='plain', axis='y', useOffset=False)
                plt.title(f"Throughput performance - {protocol} targeting {bw[:len(bw)-1]}Mb/s")
                # sub["packets"].sort()
                plt.plot(sub["packets"], tt, label=f"{kernel}")
            ax = plt.gca()
            ax.yaxis.set_major_formatter('{x:9<5.1f}')
            ax.legend()
            plt.savefig(f"../results/{results.machinename}-mt-{bw}-{protocol}-throughput.png")

def iperf3_mt_graphs_cpu(results):
    """
    Generates plots of CPU utilisation against packet size for UDP/TCP results
    """
    for protocol in ["UDP", "TCP"]:
        for bw in results.bws:
            plt.clf()
            y_range = []
            for kernel in results.kernels:
                # print(f"Graphing {protocol}-{bw}-{kernel}")
                sub = {}
                if protocol == "UDP":
                    sub = results.get_mt_result(bw, True, kernel)
                else:
                    sub = results.get_mt_result(bw, False, kernel)
                if len(sub["cpu"]) == 0:
                    continue
                
                for cpu in sub["cpu"]:
                    if cpu not in y_range:
                        y_range.append(cpu)
                
                plt.xlabel("Packet sizes (bytes)")
                plt.ylabel("CPU Utilisation (%)")
                # plt.ticklabel_format(style='plain', axis='y', useOffset=False)
                plt.title(f"Mean CPU Utilisation (per core) - {protocol} targeting {bw[:len(bw)-1]}Mb/s")
                # sub["packets"].sort()
                plt.plot(sub["packets"], sub["cpu"], label=f"{kernel}")
            plt.yticks(ticks(y_range, 10))
            ax = plt.gca()
            ax.yaxis.set_major_formatter('{x:9<5.1f}')
            ax.legend()
            plt.savefig(f"../results/{results.machinename}-mt-{bw}-{protocol}-cpu.png")

def iperf3_mt_graphs_latency(results):
    """
    Generates plots of latency against packet size for TCP results
    """
    for protocol in ["TCP"]:
        for bw in results.bws:
            plt.clf()
            y_range = []
            for kernel in results.kernels:
                # print(f"Graphing {protocol}-{bw}-{kernel}")
                sub = {}
                sub = results.get_mt_result(bw, False, kernel)
                if len(sub["latency"]) == 0:
                    continue
                
                for latency in sub["latency"]:
                    if latency not in y_range:
                        y_range.append(latency)
                
                plt.xlabel("Packet sizes (bytes)")
                plt.ylabel("Packet RTT (us)")
                # plt.ticklabel_format(style='plain', axis='y', useOffset=False)
                plt.title(f"Mean RTT latency per-core - {protocol} targeting {bw[:len(bw)-1]}Mb/s")
                # sub["packets"].sort()
                plt.plot(sub["packets"], sub["latency"], label=f"{kernel}")
            plt.yticks(ticks(y_range, 10))
            ax = plt.gca()
            ax.yaxis.set_major_formatter('{x:9<5.1f}')
            ax.legend()
            plt.savefig(f"../results/{results.machinename}-mt-{bw}-{protocol}-latency.png")



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
    return int(file.split("-")[4].split(".")[0])


# everything below this line is bad and needs to be replaced
class iperf_results():
    def __init__(self, results, machinename):
        self.results = results
        pkt_sizes_udp = []
        pkt_sizes_tcp = []
        self.machinename = machinename
        kernels = []
        bws = []
        # Check packet sizes in the first test for both UDP and TCP
        for kernel in results:
            if kernel not in kernels:
                kernels.append(kernel)
            for bw in results[kernel]["st"]["TCP"]:
                if bw not in bws:
                    bws.append(bw)
                for test in results[kernel]["st"]["TCP"][bw]:
                    if test["packet_sz"] not in pkt_sizes_tcp:
                        pkt_sizes_tcp.append(test["packet_sz"])
            for bw in results[kernel]["st"]["UDP"]:
                if bw not in bws:
                    bws.append(bw)    
                for test in results[kernel]["st"]["UDP"][bw]:
                    if test["packet_sz"] not in pkt_sizes_udp:
                        pkt_sizes_udp.append(test["packet_sz"])
        # hacky but whatever
        self.sizes_udp = pkt_sizes_udp
        self.sizes_tcp = pkt_sizes_tcp
        self.bws = bws
        self.kernels = kernels
    
    def get_st_result(self, bw, udp, kernel):
        throughput = []
        latency = []
        cpu = []
        packets = []
        if not udp:
            for test in self.results[kernel]["st"]["TCP"][bw]:
                throughput.append(float(test["end"]["sum_sent"]["bits_per_second"]) / 10**6)
                latency.append(test["end"]["streams"][0]["sender"]["mean_rtt"])
                cpu.append(test["end"]["cpu_utilization_percent"]["remote_total"])
                packets.append(test["packet_sz"])
            return {"throughput" : throughput, "latency" : latency, "cpu" : cpu, "packets" : packets}
        else:
            try:
                for test in self.results[kernel]["st"]["UDP"][bw]:
                    throughput.append(float(test["end"]["sum_sent"]["bits_per_second"]) / 10**6)
                    cpu.append(test["end"]["cpu_utilization_percent"]["remote_total"])
                    packets.append(test["packet_sz"])
            except:
                print(f"failed to open {bw}")
            return {"throughput" : throughput, "cpu" : cpu, "packets" : packets}
    
    def get_result_st_udp(self, bw, kernel):
        return self.get_st_result(bw, True, kernel)

    def get_result_st_tcp(self, bw, kernel):
        return self.get_st_result(bw, False, kernel)

    def get_mt_result(self, bw, udp, kernel):
        """
        Returns an averaged set of results from a group of multithreaded results
        """
        throughput = []
        latency = []
        cpu = []
        pkt_sizes = []

        if not udp:
            subtasks = []
            for subtask in self.results[kernel]["mt"]["TCP"]:
                subtasks.append(subtask)
            
            # print(self.results[kernel]["st"]["TCP"])
            # Iterate over the top level bandwidth, under the assumption that they match for all. They always *should*
            for test in range(0, len(self.results[kernel]["mt"]["TCP"][subtask][bw])):
                subthru = []
                sublat = []
                subcpu = []
                for s in subtasks:
                    subthru.append(float(self.results[kernel]["mt"]["TCP"][subtask][bw][test]["end"]["sum_sent"]["bits_per_second"]) / 10**6)
                    subcpu.append(float(self.results[kernel]["mt"]["TCP"][subtask][bw][test]["end"]["cpu_utilization_percent"]["remote_total"]))
                    sublat.append(self.results[kernel]["mt"]["TCP"][subtask][bw][test]["end"]["streams"][0]["sender"]["mean_rtt"])
                    if self.results[kernel]["mt"]["TCP"][subtask][bw][test]["packet_sz"] not in pkt_sizes:
                        pkt_sizes.append(self.results[kernel]["mt"]["TCP"][subtask][bw][test]["packet_sz"])
                    
                throughput.append(sum(subthru))
                cpu.append(mean(subcpu))
                latency.append(mean(sublat))
            pkt_sizes.sort(key=lambda pkt: int(pkt))
            return {"throughput" : throughput, "latency" : latency, "cpu" : cpu, "packets" : pkt_sizes}
        else:
            subtasks = []
            for subtask in self.results[kernel]["mt"]["UDP"]:
                subtasks.append(subtask)
            
            # this will crash with any incoherency in the json at all
            for test in range(0, len(self.results[kernel]["mt"]["UDP"][subtask][bw])):
                subthru = []
                subcpu = []
                for s in subtasks:
                    subthru.append(float(self.results[kernel]["mt"]["UDP"][subtask][bw][test]["end"]["sum_sent"]["bits_per_second"]) / 10**6)
                    subcpu.append(float(self.results[kernel]["mt"]["UDP"][subtask][bw][test]["end"]["cpu_utilization_percent"]["remote_total"]))
                    if self.results[kernel]["mt"]["UDP"][subtask][bw][test]["packet_sz"] not in pkt_sizes:
                        pkt_sizes.append(self.results[kernel]["mt"]["UDP"][subtask][bw][test]["packet_sz"])
                    
                throughput.append(sum(subthru))
                cpu.append(sum(subcpu))
            pkt_sizes.sort(key=lambda pkt: int(pkt))
            # print(pkt_sizes)
            return {"throughput" : throughput, "cpu" : cpu, "packets" : pkt_sizes}


    # def mean_throughput_by_major(self, bw, udp):
    #     # Get best performing throughput for each major version
        

# For testingg
if __name__ == "__main__":
    import sys
    finalise_iperf3("/home/mattr/tor-scripts/kernelmark/output", sys.argv[1])
