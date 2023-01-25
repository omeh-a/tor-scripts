import sys
import os
import json

def main():
    # Print the received and send throughput from the json files
    for kernel in os.listdir("."):
        if os.path.isfile(kernel):
            continue

        for file in os.listdir(kernel):
            if "iperf3" in file and file.split("-")[1] == "st":
                with open(f"{kernel}/{file}") as f:
                    print(f"Kernel {kernel} - {file}")
                    j = json.load(f)
                    # if "udp" in file:
                    sender = j["end"]["sum_sent"]["bits_per_second"]
                    receiver = j["end"]["sum_received"]["bits_per_second"]
                    cpu = j["end"]["cpu_utilization_percent"]["host_total"]
                    print(f"Sender: {sender}")
                    print(f"Receiver: {receiver}")
                    print(f"CPU: {cpu}")
                    # else:
                    #     sender = j["end"]["sum_sent"]["bits_per_second"]
                    #     receiver = j["end"]["sum_received"]["bits_per_second"]
                    #     print(f"Sender: {sender}")

                    #     print(f"Receiver: {receiver}")

                print('\n')

if __name__ == "__main__":
    main()