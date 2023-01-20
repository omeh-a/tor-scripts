# finalise
#   Script to collect and collate test results, generate graphs.
#   Works as a standalone script - see __main__ statement.
# Matt Rossouw (omeh-a)
# 01/23

import matplotlib.pyplot as plt
import json
import os
from statistics import mean
from test import MAX_PKT_SZ
import csv

IDEAL_LATENCY = 0.005
IPBENCH_PKTSIZES = [
    1448, 1217, 1120, 1056, 1024, 1000, 861, 800, 724, 680, 608, 590,
    580, 512, 430, 362, 304, 256, 215, 181, 152, 128, 90, 76, 64
]
IPBENCH_OUTPUT_COLUMNS = [
    "Requested throughput", "Achieved throughput", "Sent size", "Minimum",
    "Average", "Max", "Standard deviation", "Median"
]


def finalise_ipbench(out_dir, machine_name, sender):
    """
    Retrieve unmarshalled results from machine by kernel version and generate graphs.
    """

    plt.clf()
    y_range = []
    x_range = []
    key = "received"
    if sender:
        key = "sent"

    for kernel in os.listdir(f"{out_dir}/{machine_name}"):
        print(kernel)
        if not os.path.exists(f"{out_dir}/{machine_name}/{kernel}/ipbench_result"):
            print(f"No ipbench results for kernel {kernel}!")
            continue

        csv = ipbench_csv(f"{out_dir}/{machine_name}/{kernel}/ipbench_result")
        requested = []
        achieved = []

        # Plot requested vs. achieved throughput
        for i in range(0, len(csv["Requested-throughput"])):
            requested.append(csv["Requested-throughput"][i])
            achieved.append(csv[f"Achieved-throughput-{key}"][i])

            # Ranging info
            if csv[f"Achieved-throughput-{key}"][i] not in y_range:
                y_range.append(csv[f"Achieved-throughput-{key}"][i])
            if csv["Requested-throughput"][i] not in x_range:
                x_range.append(csv["Requested-throughput"][i])
                x_range.append(csv["Achieved-throughput-sent"][i])
            # convert to megabits
        for i in range(len(requested)):
            requested[i] = int(requested[i]) / (10**6)
            achieved[i] = int(achieved[i]) / (10**6)
        print(f"Requested: {requested} \n Achieved: {achieved}")
        plt.plot(requested, achieved, label=f"{kernel} - {key}")

    
    if x_range == [] or y_range == []:
        print("No results! Exiting")
        exit(0)
    
    # convert axes to megabits
    for i in range(len(x_range)):
        x_range[i] = int(x_range[i]) / 10**6
    for i in range(len(y_range)):
        y_range[i] = int(y_range[i]) / 10**6
    
    
    plt.xlabel("Requested throughput (MBit/s)")
    plt.ylabel("Achieved throughput (MBit/s)")
    plt.title(f"{machine_name} {kernel} - ipbench Requested vs Achieved throughput ({key})")
    plt.yticks(ticks(y_range, 10))
    plt.xticks(ticks(x_range, 10))
    ax = plt.gca()
    ax.legend()
    ax.yaxis.set_major_formatter('{x:9<5.1f}')
    plt.savefig(f"../results/{machine_name}-{key}-ipbench.png")

def ipbench_csv(path):
    """
    Python's csv library is awful apparently so I need to do this myself.
    Given a csv file with the first row containing headers, return a dict
    """
    out = {}
    with open(path, "r") as f:
        first = True
        headers = []
        for row in f:
            # get headers from first row
            if first:
                first = False
                for term in row.split(','):
                    headers.append(term)
                    out[term] = []
            # get rest
            else:
                i = 0
                for term in row.split(','):
                    out[headers[i]].append(term)
                    i += 1
    return out
    # now how hard was that? why can the python csv library not find the headers properly??





def finalise_iperf3(out_dir, machine_name):
    """
    Generate iperf3 results for all available result files
    """
    
    results = {}
    
    # Find all tests
    for kernel in os.listdir(f"{out_dir}/{machine_name}"):
        # sub = []
        # Open each test
        try:
            _ = results[kernel]
        except KeyError:
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
                        # print(f"Added bw {bw}")
                        results[kernel]["st"][protocol][bw] = []
                        results[kernel]["st"][protocol][bw].append(result)
                # otherwise, for multithreaded we need to break this up further
                # yes i know this json stuff is a nightmare, but this saves having to reformat every single entry
                else:
                    # check this mt has an entry
                    try:
                        _ = results[kernel]["mt"][protocol][file.split("-")[1]]
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
    iperf3_st_graphs_throughput(r, True)
    iperf3_st_graphs_throughput(r, False)
    iperf3_st_graphs_latency(r)
    iperf3_st_graphs_cpu(r)
    iperf3_mt_graphs_throughput(r)
    iperf3_mt_graphs_cpu(r)
    iperf3_mt_graphs_latency(r)
    iperf3_st_graph_appliedactual(r)
    iperf3_st_graphs_sendrecv_throughput(r)
    

def iperf3_st_graphs_throughput(results, reverse):
    """
    Generates plots of throughput against packet size for UDP/TCP results
    """
    throughput_type = "throughput"
    if reverse:
        throughput_type = "throughput_reverse"
    for protocol in ["UDP", "TCP"]:
        for bw in ["1000m"]:
            plt.clf()
            y_range = []
            for kernel in results.kernels:
                print(f"Graphing {protocol}-{bw}-{kernel}")
                sub = {}
                if protocol == "UDP":
                    sub = results.get_result_st_udp(bw, kernel)
                else:
                    sub = results.get_result_st_tcp(bw, kernel)
                if len(sub[throughput_type]) == 0:
                    continue
                
                for t in sub[throughput_type]:
                    if t not in y_range:
                        y_range.append(t)

                
                plt.xlabel("Packet sizes (bytes)")
                plt.ylabel("Throughput (MBit/s)")
                #pkt_ticks(packet_sizes)
                # plt.ticklabel_format(style='plain', axis='y', useOffset=False)
                plt.title(f"{results.machinename} - ST {throughput_type} performance - {protocol} targeting {bw[:len(bw)-1]}Mb/s")
                plt.plot(sub["packets"], sub[throughput_type], label=f"{kernel}")
            plt.yticks(ticks(y_range, 10))
            ax = plt.gca()
            ax.yaxis.set_major_formatter('{x:9<5.1f}')
            ax.legend()
            plt.savefig(f"../results/{results.machinename}-st-{bw}-{protocol}-{throughput_type}.png")

def iperf3_st_graphs_latency(results):
    """
    Generates plots of latency against packet size for TCP results
    """
    for protocol in ["TCP"]:
        for bw in ["1000m"]:
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
                plt.title(f"{results.machinename} - ST Latency - {protocol} targeting {bw}b/s")
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
        for bw in ["1000m"]:
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
                plt.title(f"{results.machinename} - ST CPU Utilisation - {protocol} targeting {bw[:len(bw)-1]}Mb/s")
                plt.plot(sub["packets"], sub["cpu"], label=f"{kernel}")
            plt.yticks(ticks(y_range, 10))
            ax = plt.gca()
            ax.yaxis.set_major_formatter('{x:9<5.1f}')
            ax.legend()
            plt.savefig(f"../results/{results.machinename}-st-{bw}-{protocol}-cpu.png")               

def iperf3_st_graphs_sentrecv_thru(results):
    """
    Generates plots of bidirectional throughput against packet size for UDP/TCP results
    """
    for protocol in ["UDP", "TCP"]:
        for bw in ["1000m"]:
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
                plt.title(f"{results.machinename} - ST bidir Throughput performance - {protocol} targeting {bw[:len(bw)-1]}Mb/s")
                plt.plot(sub["packets"], tt, label=f"{kernel}")
                plt.plot(sub["packets"], sub["throughput_reversed"], "o", label=f"{kernel} Reversed")
            ax = plt.gca()
            ax.yaxis.set_major_formatter('{x:9<5.1f}')
            ax.legend()
            plt.savefig(f"../results/{results.machinename}-st-{bw}-{protocol}-throughput.png")

def iperf3_mt_graphs_throughput(results):
    """
    Generates plots of throughput against packet size for UDP/TCP results
    """
    for protocol in ["UDP", "TCP"]:
        for bw in ["1000m"]:
            plt.clf()
            y_range = []
            for kernel in results.kernels:
                # print(f"Graphing {protocol}-{bw}-{kernel}")
                sub = {}
                if protocol == "UDP":
                    sub = results.get_mt_result(bw, True, kernel)
                else:
                    sub = results.get_mt_result(bw, False, kernel)
                if len(sub["throughput"]) == 0:
                    continue
                for t in sub["throughput"]:
                    if t not in y_range:
                        y_range.append(t)
                
                plt.xlabel("Packet sizes (bytes)")
                # tt = unitise_plot(sub["throughput"], "Throughput")
                plt.ylabel("Throughput (MBit/s)")
                #pkt_ticks(packet_sizes)
                # plt.ticklabel_format(style='plain', axis='y', useOffset=False)
                plt.title(f"{results.machinename} - MT Aggregate Throughput performance - {protocol} targeting {bw[:len(bw)-1]}Mb/s")
                # print(sub["packets"])
                # sub["packets"].sort()
                plt.plot(sub["packets"], sub["throughput"], label=f"{kernel}")
            plt.yticks(ticks(y_range, 10))
            ax = plt.gca()
            ax.yaxis.set_major_formatter('{x:9<5.1f}')
            ax.legend()
            plt.savefig(f"../results/{results.machinename}-mt-{bw}-{protocol}-throughput.png")

def iperf3_mt_graphs_cpu(results):
    """
    Generates plots of CPU utilisation against packet size for UDP/TCP results
    """
    for protocol in ["UDP", "TCP"]:
        for bw in ["1000m"]:
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
                plt.title(f"{results.machinename} - MT Mean CPU Utilisation (per core) - {protocol} targeting {bw[:len(bw)-1]}Mb/s")
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
        for bw in ["1000m"]:
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
                plt.title(f"{results.machinename} - MT Mean RTT latency (per-core) - {protocol} targeting {bw[:len(bw)-1]}Mb/s")
                # sub["packets"].sort()
                plt.plot(sub["packets"], sub["latency"], label=f"{kernel}")
            plt.yticks(ticks(y_range, 10))
            ax = plt.gca()
            ax.yaxis.set_major_formatter('{x:9<5.1f}')
            ax.legend()
            plt.savefig(f"../results/{results.machinename}-mt-{bw}-{protocol}-latency.png")

def iperf3_st_graph_appliedactual(results):
    """
    Generates plots of throughput against packet size for UDP/TCP results
    """
    for protocol in ["UDP", "TCP"]:
        plt.clf()
        for kernel in results.kernels:
            result = results.get_st_appliedactual((protocol == "UDP"), kernel)
            print(result)
            if result == [] or result["throughput"] == []: 
                continue  
            plt.xlabel("Target bandwidth  (MBit/s)")
            tt = unitise_plot(result["throughput"], "Actual bandwidth (Mbit/s)")
            #pkt_ticks(packet_sizes)
            plt.yticks(ticks(tt, 10))
            # plt.ticklabel_format(style='plain', axis='y', useOffset=False)
            plt.title(f"{results.machinename} - Target vs. actual bandwidth - {protocol}")
            plt.plot(result["bw"], tt, label=f"{kernel}")
        ax = plt.gca()
        ax.yaxis.set_major_formatter('{x:9<5.1f}')
        ax.legend()
        plt.savefig(f"../results/{results.machinename}-st-{kernel}-appliedactual-{protocol}.png")

def iperf3_st_graphs_sendrecv_throughput(results):
    """
    Generates plots of throughput against packet size for UDP/TCP results with separate graphs
    for send/receive
    """
    for protocol in ["UDP", "TCP"]:
        for bw in ["1000m"]:
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
                plt.title(f"{results.machinename} - ST Throughput performance - {protocol} targeting {bw[:len(bw)-1]}Mb/s")
                plt.plot(sub["packets"], tt, label=f"{kernel}")
                plt.plot(sub["packets"], sub["throughput_reverse"], "o", label=f"{kernel} reversed",)
            ax = plt.gca()
            ax.yaxis.set_major_formatter('{x:9<5.1f}')
            ax.legend()
            plt.savefig(f"../results/{results.machinename}-st-{bw}-{protocol}-bidir.png")

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



class iperf_results():
    def __init__(self, out_dir, machine_name):
        """
        Take location, collate tests.

        Dict formats for st/mt tests:
        {
            bandwidth : [tests sorted by packet size],
            bandwidth1 : ...
            ...

        }

        For MT, there is another array wrapping above this structure

        Tests:
        {
            "packet_sz" : packet size,
            "rtt" : mean rtt,
            "cpu" : target cpu utilisation (mean)
            "throughput_send": mean throughput over all runs, sender. If monodirectional test this becomes only field for tp.
            "throughput_receive": mean throughput over all runs, receiver.
            "raw" : raw json of test
        }
        """
        
        self.udp_st_tests = {}
        self.udp_mt_tests = []
        self.tcp_st_tests = {}
        self.tcp_mt_tests = []

        # Find all tests
        for kernel in os.listdir(f"{out_dir}/{machine_name}"):
            for test in os.listdir(f"{out_dir}/{machine_name}/{kernel}"):
                if not ".test" in test or not "iperf3" in test:
                    continue
                with open(f"{out_dir}/{machine_name}/{kernel}/{test}") as f:
                    try:
                        result = json.load(f)
                    except:
                        print(f"Failed to open {machine_name} - {kernel} {test}")
                        continue

                    if len(result["intervals"]) == 0:
                        print(f"Test {machine_name} - {kernel} {test} failed to run. Skipping.")
                        continue
                    
                    # extract bandwidth
                    bw = test.split("-")[3].split("m")[0]

                    test = {
                        "packet_sz" : test.split("-")[3],
                        "rtt" : result["end"]["streams"][0]["sender"]["mean_rtt"],
                        "cpu" : result["end"]["cpu_utilization_percent"]["host_total"],
                        "throughput_send" : float(result["end"]["sum_sent"]["bits_per_second"] / (10**6)),
                        "throughput_receive" : float(result["end"]["sum_sent_bidir_reverse"]["bits_per_second"] / (10**6)),
                        "raw" : result
                    }

                    # check for mt/st
                    if test.split("-")[1] == "st":
                        # protocol
                        if test.split("-")[2] == "udp":
                            self.udp_st_tests = self.append_dict(self.udp_st_tests, test, bw, -1)
                        else:
                            self.tcp_st_tests = self.append_dict(self.tcp_st_tests, test, bw, -1)
                    else:
                        mt_num = int(test.split("-")[1].split("mt")[1]) - 1
                        if test.split("-")[2] == "udp":
                            self.udp_mt_tests = self.append_dict(self.udp_mt_tests, test, bw, mt_num)
                        else:
                            self.tcp_mt_tests = self.append_dict(self.tcp_mt_tests, test, bw, mt_num)
    
    
    def append_dict(self, target, test, bw, mt):
        """
        Append a test to an internal dict. Returns the modified dict
        """

        # ST case
        if mt == -1:
            # Check that target bw exists
            try:
                _ = target[bw]
            except KeyError:
                target[bw] = []

            # Insert
            target[bw].append(test)
        
        # MT case
        else:
            # Check if we have at least n entries in the MT array
            while len(target) < mt:
                target.append({})
            
            # Check that target bw exists
            try:
                _ = target[mt][bw]
            except KeyError:
                target[mt][bw] = []

            # Insert
            target[mt][bw].append(test)

        return target





# For testingg
if __name__ == "__main__":
    out_dir = "/home/mattr/tor-scripts/kernelmark/output"
    import sys
    if len(sys.argv) < 3:
        print("USAGE: finalise.py [machine] [test1] ... [test n] \n tests: ipbench, iperf3")
    
    if "ipbench" in sys.results = {}
    
    # Find all tests
    for kernel in os.listdir(f"{out_dir}/{machine_name}"):
        # sub = []
        # Open each test
        try:
            _ = results[kernel]
        except KeyError:argv:
        finalise_ipbench(out_dir, sys.argv[1], True)
        finalise_ipbench(out_dir, sys.argv[1], False)
    if "iperf3" in sys.argv:
        finalise_iperf3(out_dir, sys.argv[1])
results = {}
    
    # Find all tests
    for kernel in os.listdir(f"{out_dir}/{machine_name}"):
        # sub = []
        # Open each test
        try:
            _ = results[kernel]
        except KeyError: