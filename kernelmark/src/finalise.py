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
THROUGHPUT_BENCH_BW = 1000
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
    r = iperf_results(out_dir, machine_name)
    # everything in the name of compactness
    for cond in [(False, False), (False, True), (True, True)]:
        iperf3_st_pktsz_throughput(r, cond[0], cond[1])
        iperf3_st_bw_throughput(r, cond[0], cond[1])
        # iperf3_mt_bw_throughput(r, cond[0], cond[1])
        if cond[1]:
            iperf3_st_bw_cpu(r, cond[0])
            iperf3_st_bw_latency(r, cond[0])


def iperf3_st_pktsz_throughput(results, reverse, bidir):
    """
    Generates plots of throughput against packet size for UDP/TCP results
    """
    throughput_type = "throughput_send"
    if reverse:
        throughput_type = "throughput_receive"

    for tcp in [True, False]:
        if len(results.tcp_st_tests) != 0:
            print(f"{results.machinename} - ST Throughtput - TCP targeting 1000Mb/s")
            plt.clf()
            y_largest_range = []
            for kernel in results.kernels:
                test = None
                if tcp:
                    test = results.get_st_test_pktsize_tcp(kernel)
                else:
                    test = results.get_st_test_pktsize_udp(kernel)
                if test == None:
                    continue
                
                for element in test[throughput_type]:
                    y_largest_range.append(element)


                plt.plot(test["pkt_szs"], test[throughput_type], label=f"{kernel}")
            plt.xlabel("Packet sizes (bytes)")
            plt.ylabel("Throughput (MBit/s)")
            label = "UDP"
            if tcp:
                label = "TCP"
            
            plt.title(f"{results.machinename} - ST Throughtput - {label} targeting 1000Mb/s")
            plt.yticks(ticks(y_largest_range, 10))
            ax = plt.gca()
            ax.yaxis.set_major_formatter('{x:9<5.1f}')
            ax.legend()

            if bidir: throughput_type += "-bidir"
            s = f"../results/{results.machinename}-st-pktsz-1000m-{label}-{throughput_type}.png"
            plt.savefig(s)  
            print(f"Saved {s}")


def iperf3_st_pktsize_latency(results):
    """
    Generates plots of latency against packet size for TCP results
    """
    plt.clf()
    y_largest_range = []
    for kernel in results.kernels:
        test = results.get_st_test_pktsize_tcp(kernel)
        if test == None:
            continue
        
        if test.bidir:
            continue

        print(test)
        # print(test[0])

        # if y_largest_range == [] or max(y_largest_range) < max(test[throughput_type]):
        for element in test["rtt"]:
            y_largest_range.append(element)

        plt.xlabel("Packet sizes (bytes)")
        plt.ylabel("Latency (us)")
        # plt.ticklabel_format(style='plain', axis='y', useOffset=False)
        plt.plot(test["pkt_szs"], test["rtt"], label=f"{kernel}")
    plt.title(f"{results.machinename} - ST Latency - TCP targeting 1000Mb/s")
    plt.yticks(ticks(y_largest_range, 10))
    ax = plt.gca()
    ax.yaxis.set_major_formatter('{x:9<5.1f}')
    ax.legend()
    s = f"../results/{results.machinename}-st-1000m-rtt.png"
    plt.savefig(s)  
    print(f"Saved {s}")
               

def iperf3_st_pktsize_cpu(results):
    """
    Generates plots of cpu against packet size for UDP/TCP results
    """
    # TCP
    plt.clf()
    y_largest_range = []
    for kernel in results.kernels:
        test = results.get_st_test_pktsize_tcp(kernel)
        if test == None:
            continue
        
        if test == None:
            continue
        
        if test.bidir:
            continue

        for element in test["cpu"]:
            y_largest_range.append(element)

        plt.xlabel("Packet sizes (bytes)")
        plt.ylabel("CPU utilisation (%)")
        #pkt_ticks(packet_sizes)
        # plt.ticklabel_format(style='plain', axis='y', useOffset=False)
        plt.plot(test["pkt_szs"], test["cpu"], label=f"{kernel}")
    plt.title(f"{results.machinename} - ST CPU - TCP targeting 1000Mb/s")
    plt.yticks(ticks(y_largest_range, 10))
    ax = plt.gca()
    ax.yaxis.set_major_formatter('{x:9<5.1f}')
    ax.legend()
    s = f"../results/{results.machinename}-st-1000m-TCP-cpu.png"
    plt.savefig(s)
    print(f"Saved {s}")

    # UDP
    plt.clf()
    y_largest_range = []
    for kernel in results.kernels:
        test = results.get_st_test_pktsize_udp(kernel)
        if test == None:
            continue
        

        print(test)
        # print(test[0])

        # if y_largest_range == [] or max(y_largest_range) < max(test[throughput_type]):
        for element in test["cpu"]:
            y_largest_range.append(element)

        plt.xlabel("Packet sizes (bytes)")
        plt.ylabel("CPU utilisation (%)")
        #pkt_ticks(packet_sizes)
        # plt.ticklabel_format(style='plain', axis='y', useOffset=False)
        plt.plot(test["pkt_szs"], test["cpu"], label=f"{kernel}")
    plt.title(f"{results.machinename} - ST Throughtput - UDP targeting 1000Mb/s")
    plt.yticks(ticks(y_largest_range, 10))
    ax = plt.gca()
    ax.yaxis.set_major_formatter('{x:9<5.1f}')
    ax.legend()
    s = f"../results/{results.machinename}-st-1000m-UDP-CPU.png"
    plt.savefig(s)  
    print(f"Saved {s}")           

def iperf3_mt_pktsize_throughput(results, ):
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

def iperf3_mt_pktsize_cpu(results):
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

def iperf3_mt_pktsize_latency(results):
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

def iperf3_st_bw_throughput(results, reverse, bidir):
    """
    Generates plots of throughput against target bandwidth for UDP/TCP results
    """
    throughput_type = "throughput_send"
    if reverse:
        throughput_type = "throughput_receive"
    for tcp in [True, False]:
        label = "UDP"
        if tcp:
            label = "TCP"
        
        if reverse:
            label += " reverse"
        if bidir:
            label += " bidir"

        print(f"{results.machinename} - ST {label} Throughtput - targeting 1000Mb/s")
        plt.clf()
        y_largest_range = []
        tests_exist = False
        for kernel in results.kernels:
            test = None
            if tcp:
                test = results.get_st_test_bw_tcp(kernel, bidir)
            else:
                test = results.get_st_test_bw_udp(kernel, bidir)
            if test == None:
                continue
            tests_exist = True

            for element in test[throughput_type]:
                y_largest_range.append(element)

            print(test)
            plt.plot(test["bws"], test[throughput_type], label=f"{kernel}")
        
        if not tests_exist: continue
        
        plt.xlabel("Requested throughput (MBit/s)")
        plt.ylabel("Actual Throughput (MBit/s)")
        
        plt.title(f"{results.machinename} - ST Throughtput vs BW - {label} targeting 1000Mb/s")
        plt.yticks(ticks(y_largest_range, 10))
        ax = plt.gca()
        ax.yaxis.set_major_formatter('{x:9<5.1f}')
        ax.legend()

        if bidir: throughput_type += "-bidir"
        s = f"../results/{results.machinename}-st-1000m-bw-{label}-{throughput_type}.png"
        plt.savefig(s)  
        print(f"Saved {s}")

def iperf3_mt_bw_throughput(results, reverse, bidir):
    """
    Generates plots of throughput against target bandwidth for UDP/TCP results
    """
    throughput_type = "throughput_send"
    if reverse:
        throughput_type = "throughput_receive"
    for tcp in [True, False]:
        label = "UDP"
        if tcp:
            label = "TCP"
        
        if reverse:
            label += " reverse"
        if bidir:
            label += " bidir"

        print(f"{results.machinename} - ST {label} Throughtput - targeting 1000Mb/s")
        plt.clf()
        y_largest_range = []
        tests_exist = False
        for kernel in results.kernels:
            test = None
            if tcp:
                test = results.get_mt_test_bw_udp(kernel, bidir)
            else:
                test = results.get_mt_test_bw_udp(kernel, bidir)
            if test == None:
                continue
            tests_exist = True

            for element in test[throughput_type]:
                y_largest_range.append(element)

            print(test)
            plt.plot(test["bws"], test[throughput_type], label=f"{kernel}")
        
        if not tests_exist: continue
        
        plt.xlabel("Requested throughput (MBit/s)")
        plt.ylabel("Actual Throughput (MBit/s)")
        
        plt.title(f"{results.machinename} - MT Throughtput vs BW - {label} targeting 1000Mb/s")
        plt.yticks(ticks(y_largest_range, 10))
        ax = plt.gca()
        ax.yaxis.set_major_formatter('{x:9<5.1f}')
        ax.legend()

        if bidir: throughput_type += "-bidir"
        s = f"../results/{results.machinename}-mt-1000m-bw-{label}-{throughput_type}.png"
        plt.savefig(s)  
        print(f"Saved {s}")

def iperf3_st_bw_cpu(results, bidir):
    """
    Generates plots of throughput against target bandwidth for UDP/TCP results
    """
    for tcp in [True, False]:
        label = "UDP"
        if tcp:
            label = "TCP"
        if bidir:
            label += " bidir"

        print(f"{results.machinename} - ST {label} CPU")
        plt.clf()

        tests_exist = False
        for kernel in results.kernels:
            test = None
            if tcp:
                test = results.get_st_test_bw_tcp(kernel, bidir)
            else:
                test = results.get_st_test_bw_udp(kernel, bidir)
            if test == None:
                continue
            tests_exist = True

            plt.plot(test["bws"], test["cpu"], label=f"{kernel}")
        
        if not tests_exist: continue
        
        plt.xlabel("Requested throughput (MBit/s)")
        plt.ylabel("CPU utilisation (%)")
        
        plt.title(f"{results.machinename} - ST CPU utilisation vs BW - {label}")
        ax = plt.gca()
        ax.yaxis.set_major_formatter('{x:9<5.1f}')
        ax.legend()
        s = f"../results/{results.machinename}-st-1000m-bw-{label}-cpu.png"
        plt.savefig(s)  
        print(f"Saved {s}")
    
def iperf3_st_bw_latency(results, bidir):
    """
    Generates plots of throughput against target bandwidth for UDP/TCP results
    """
    for tcp in [True, False]:
        label = "UDP"
        if tcp:
            label = "TCP"
        if bidir:
            label += " bidir"

        print(f"{results.machinename} - ST {label} CPU")
        plt.clf()

        tests_exist = False
        for kernel in results.kernels:
            test = None
            if tcp:
                test = results.get_st_test_bw_tcp(kernel, bidir)
            else:
                test = results.get_st_test_bw_udp(kernel, bidir)
            if test == None:
                continue
            tests_exist = True

            plt.plot(test["bws"], test["rtt"], label=f"{kernel}")
        
        if not tests_exist: continue
        
        plt.xlabel("Requested throughput (MBit/s)")
        plt.ylabel("Mean RTT (us)")
        
        plt.title(f"{results.machinename} - ST Mean RTT vs BW - {label}")
        ax = plt.gca()
        ax.yaxis.set_major_formatter('{x:9<5.1f}')
        ax.legend()
        s = f"../results/{results.machinename}-st-1000m-bw-{label}-rtt.png"
        plt.savefig(s)  
        print(f"Saved {s}")


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
            kernel1 : {
                bandwidth : [tests sorted by packet size],
                bandwidth1 : ...
                ...
            } ... 

        }

        For MT, there is another array wrapping above this structure

        Tests:
        {
            "packet_sz" : packet size,
            "bw" : target bandwidth,
            "rtt" : mean rtt,
            "cpu" : target cpu utilisation (mean)
            "throughput_send": mean throughput over all runs, sender. If monodirectional test this becomes only field for tp.
            "throughput_receive": mean throughput over all runs, receiver.
            "raw" : raw json of test
            "bidir" : True if this test is bidirectional
        }
        """
        self.udp_st_tests = {}
        self.udp_mt_tests = []
        self.tcp_st_tests = {}
        self.tcp_mt_tests = []
        self.kernels = []
        self.machinename = machine_name
        # Find all tests
        for kernel in os.listdir(f"{out_dir}/{machine_name}"):
            self.kernels.append(kernel)
            for iperf_out in os.listdir(f"{out_dir}/{machine_name}/{kernel}"):
                if not ".test" in iperf_out or not "iperf3" in iperf_out:
                    continue
                with open(f"{out_dir}/{machine_name}/{kernel}/{iperf_out}") as f:
                    try:
                        result = json.load(f)
                    except:
                        print(f"Failed to open {machine_name} - {kernel} {iperf_out}")
                        continue

                    if len(result["intervals"]) == 0:
                        print(f"Test {machine_name} - {kernel} {iperf_out} failed to run. Skipping.")
                        continue
                    
                    # extract bandwidth
                    bw = iperf_out.split("-")[3].split("m")[0]
                    protocol = iperf_out.split("-")[2].split(".")[0]
                    test = {}

                    # throughput variables -> extracted here to minimise copy pasta due to bidir handling
                    throughput_send = 0.0
                    throughput_receive = 0.0
                    if "bidir" in iperf_out.split("-")[2]:
                        throughput_send = float(result["end"]["sum_sent"]["bits_per_second"] / (10**6))
                        throughput_receive = float(result["end"]["sum_sent_bidir_reverse"]["bits_per_second"] / (10**6))
                    else:
                        throughput_send = float(result["end"]["sum_sent"]["bits_per_second"] / (10**6))
                    
                    # cpu
                    cpu = result["end"]["cpu_utilization_percent"]["host_total"]

                    # rtt
                    rtt = 0.0
                    if protocol == "tcp":
                        rtt = result["end"]["streams"][0]["sender"]["mean_rtt"]
                    else:
                        rtt = float(result["end"]["sum"]["jitter_ms"]) * 2000.0

                    test = {
                        "packet_sz" : iperf_out.split("-")[4].split(".")[0],
                        "bw" : bw,
                        "rtt" : rtt,
                        "cpu" : cpu,
                        "throughput_send" : throughput_send,
                        "throughput_receive" : throughput_receive,
                        # "raw" : result,
                        "bidir" : ("bidir" in iperf_out.split("-")[2])
                    }
                    
                    # check for mt/st
                    if iperf_out.split("-")[1] == "st":
                        # protocol
                        print(protocol)
                        if protocol == "udp":
                            self.udp_st_tests = self.append_dict(self.udp_st_tests, test, bw, -1, kernel)
                        else:
                            self.tcp_st_tests = self.append_dict(self.tcp_st_tests, test, bw, -1, kernel)
                    else:
                        mt_num = int(iperf_out.split("-")[1].split("mt")[1]) - 1
                        if protocol == "udp":
                            self.udp_mt_tests = self.append_dict(self.udp_mt_tests, test, bw, mt_num, kernel)
                        else:
                            self.tcp_mt_tests = self.append_dict(self.tcp_mt_tests, test, bw, mt_num, kernel)


    # x vs packet size tests

    def get_st_test_pktsize_udp(self, kernel, bidir):
        """
        Return tests of packet size vs. achieved throughput for UDP. Sorted by packet size
        """
        return self.get_tests_pktsz(kernel, self.udp_st_tests, bidir)

    def get_st_test_pktsize_tcp(self, kernel, bidir):
        """
        Return tests of packet size vs. achieved throughput for TCP. Sorted by packet size
        """
        return self.get_tests_pktsz(kernel, self.tcp_st_tests, bidir)
    
    def get_mt_test_pktsize_udp(self, kernel, bidir):
        """
        Return tests of packet size vs. achieved throughput for UDP. Sorted by packet size
        """
        return self.get_mt_test_pktsize(kernel, self.udp_mt_tests, bidir)
    
    def get_mt_test_pktsize_tcp(self, kernel, bidir):
        """
        Return tests of packet size vs. achieved throughput for TCP. Sorted by packet size
        """
        return self.get_mt_test_pktsize(kernel, self.tcp_mt_tests, bidir)

    def get_mt_tests_pktsize(self, kernel, in_list, bidir):
        """
        INTERNAL
        Return tests of packet size vs. achieved throughput for. Sorted by packet size
        
        Let this function show my committedness to avoiding degenerate data.
        """

        results = []
        out = []
        safe = ([], [])
        for mt in in_list:
            r = (self.get_tests_pktsz(kernel, in_list[mt], bidir))
            results.append(r)
            # Find longest entry - we treat this one as the one with the maximal set of packet sizes
            # in case others have missing tests.
            if len(r[0]) > len(safe[0]):
                safe = r

        # Sanitise data
        rr = results.copy()
        for mt in rr:
            for test in mt:
                # Check if this test has the wrong number of tests
                l = test["test"]
                if len(l) != len(safe["test"]):
                    new = safe["test"].copy()
                    # If so, create dummy list with extra elements to pad. First find bad elements by
                    # checking packet sizes
                    bad_indices = []
                    for pkt_sz in safe["pkts"]:
                        if pkt_sz not in test["pkts"]:
                            bad_indices.append(safe["pkts"].index(pkt_sz))
                    
                    # Populate new lists
                    c = 0
                    for i in range(new):
                        if i in bad_indices:
                            new[i] = -1
                        else:
                            new[i] = l[c]
                            c += 1
                    l = new
                    results[rr.index(mt)] = l
        # Average data
        for mt in results:
            out = self.mt_combine(mt, out)

        return (out, safe[1])


    def mt_combine(list1, list2, mode): 
        """
        Average/sum each element of two test sets. An element with value -1 is ignored.
        """
        if list1 == []:
            return list2
        elif list2 == []:
            return list1

        if len(list1) != len(list2):
            print("Failed to piecewise mean lists - wrong length!")
            raise ValueError
        
        out = []
        for i in range(len(list1)):
            if list1[i] != -1 and list2[i] != -1:
                if mode == "mean":
                    out.append(int((list1[i] + list2[i])/2))
                elif mode == "sum":
                    out.append(int((list1[i] + list2[i])))
            else:
                out.append(max(list1[i], list2[i]))
        return out

    def get_tests_pktsz(self, kernel, in_list, bidir):
        """
        INTERNAL
        Get tests given internal list. This function is wrapped around by the targeted ones
        """
        out = {
            "pkt_szs" : [],
            "throughput_send" : [],
            "cpu" : [],
            "throughput_receive" : [],   
            "rtt" : []
        }
        bw = None
        try:
            for bww in in_list[kernel]:
                """
                There should only be one bw with more than one test
                """
                if len(in_list[kernel][bww]) > 2:
                    bw = bww
                    print(f"Selected bw {bw}")
                    break
        except KeyError:
            print(f"WARNING: no tests for kernel {kernel}")
            return None
        if bw == None:
            print(f"WARNING: didn't find test batch with appropriate length for pktsize for\
 kernel {kernel}")
            return None
        
        tests = []

        # Collect tests
        for test in in_list[kernel][bw]:
            # !xor bidir conditions
            if (bidir and test["bidir"]) or (not bidir and not test["bidir"]):
                tests.append(test)
        # Sort
        tests.sort(key= lambda t: int(t["packet_sz"]))
        print(f"FIRST STAGE: {tests}")

        # Extract packet sizes and return separately
        pkt_szs = []
        for t in tests:
            out["pkt_szs"].append(t["packet_sz"])
            out["throughput_send"].append(t["throughput_send"])
            if t["bidir"]:
                out["throughput_receive"].append(t["throughput_receive"])

            out["cpu"].append(t["cpu"])
            try:
                out["rtt"].append(t["rtt"])
            except KeyError:
                continue
            
        
        return out

    # x vs bandwidth tests

    def get_tests_bw(self, kernel, in_list, bidir):
        """
        INTERNAL
        Get tests given internal list. This function is wrapped around by the targeted ones
        """
        out = {
            "bws" : [],
            "throughput_send" : [],
            "cpu" : [],
            "throughput_receive" : [],   
            "rtt" : []
        }

        num_bws = 0
        try:
            for bww in in_list[kernel]:
                num_bws += 1

        except KeyError:
            print(f"WARNING: no tests for kernel {kernel}")
            return None
        
        if num_bws < 2:
            print(f"WARNING: not enough tests bw graphs for kernel {kernel}")
            return None

        tests = []
        # Collect tests
        for bw in in_list[kernel]:
            for test in in_list[kernel][bw]:
                if test["packet_sz"] == str(MAX_PKT_SZ):
                    # !xor bidir conditions
                    if (bidir and test["bidir"]) or (not bidir and not test["bidir"]):        
                        tests.append(test)
        if tests == []: return None

        # Sort
        tests.sort(key= lambda t: int(t["bw"]))

        # Extract packet sizes and return separately
        pkt_szs = []
        for t in tests:
            out["bws"].append(t["bw"])
            out["throughput_send"].append(t["throughput_send"])
            if t["bidir"]:
                out["throughput_receive"].append(t["throughput_receive"])

            out["cpu"].append(t["cpu"])
            try:
                out["rtt"].append(t["rtt"])
            except KeyError:
                continue

        return out
    
    def get_mt_test_bw(self, kernel, in_list, bidir):
        """
        INTERNAL
        Return tests of bandwidth vs. achieved throughput for. Sorted by bandwidth
        
        Let this function show my committedness to avoiding degenerate data.
        """

        results = []
        out = []
        safe = ([], [])
        for mt in in_list:
            r = self.get_tests_bw(kernel, in_list[mt], bidir)
            results.append(r)
            # Find longest entry - we treat this one as the one with the maximal set of packet sizes
            # in case others have missing tests.
            if len(r[0]) > len(safe[0]):
                safe = r

        # Sanitise data
        rr = results.copy()
        for mt in rr:
            for test in mt:
                # Check if this test has the wrong number of tests
                l = test["test"]
                if len(l) != len(safe["test"]):
                    new = safe["test"].copy()
                    # If so, create dummy list with extra elements to pad. First find bad elements by
                    # checking packet sizes
                    bad_indices = []
                    for bw in safe["bw"]:
                        if bw not in test["bw"]:
                            bad_indices.append(safe["bw"].index(bw))
                    
                    # Populate new lists
                    c = 0
                    for i in range(new):
                        if i in bad_indices:
                            new[i] = -1
                        else:
                            new[i] = l[c]
                            c += 1
                    l = new
                    results[rr.index(mt)] = l
        # Average data
        for mt in results:
            out = self.mt_combine(mt, out)

        return (out, safe[1])

    def get_st_test_bw_udp(self, kernel, bidir):
        """
        Return tests of bandwidth vs. achieved throughput for UDP. Sorted by bandwidth
        """
        return self.get_tests_bw(kernel, self.udp_st_tests, bidir)

    def get_st_test_bw_tcp(self, kernel, bidir):
        """
        Return tests of bandwidth vs. achieved throughput for TCP. Sorted by bandwidth
        """
        return self.get_tests_bw(kernel, self.tcp_st_tests, bidir)
    
    def get_mt_test_bw_udp(self, kernel, bidir):
        """
        Return tests of bandwidth vs. achieved throughput for UDP. Sorted by bandwidth
        """
        return self.get_mt_test_bw(kernel, self.udp_mt_tests, bidir)
    
    def get_mt_test_bw_tcp(self, kernel, bidir):
        """
        Return tests of bandwidth vs. achieved throughput for TCP. Sorted by bandwidth
        """
        return self.get_mt_test_bw(kernel, self.tcp_mt_tests, bidir)

    def append_dict(self, target, test, bw, mt, kernel):
        """
        Append a test to an internal dict. Returns the modified dict
        """

        # ST case
        if mt == -1:
            # Check that target kernel exists
            try:
                _ = target[kernel]
            except KeyError:
                target[kernel] = {}
            
            # Check that target bw exists
            try:
                _ = target[kernel][bw]
            except KeyError:
                target[kernel][bw] = []

            # Insert
            target[kernel][bw].append(test)
        
        # MT case
        else:
            # Check if we have at least n entries in the MT array
            while len(target) <= mt:
                target.append({})
            
            # Check that target kernel exists
            try:
                _ = target[mt][kernel]
            except KeyError:
                target[mt][kernel] = {}
            
            # Check that target bw exists
            try:
                _ = target[mt][kernel][bw]
            except KeyError:
                target[mt][kernel][bw] = []

            # Insert
            target[mt][kernel][bw].append(test)

        return target


# For testingg
if __name__ == "__main__":
    out_dir = "/home/mattr/tor-scripts/kernelmark/output"
    import sys
    if len(sys.argv) < 3:
        print("USAGE: finalise.py [machine] [test1] ... [test n] \n tests: ipbench, iperf3")
    
    if "ipbench" in sys.argv:
        finalise_ipbench(out_dir, sys.argv[1])
    if "iperf3" in sys.argv:
        finalise_iperf3(out_dir, sys.argv[1])
