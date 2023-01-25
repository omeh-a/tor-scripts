import sys
import os
import json

def main():
    # Print the received and send throughput from the json files
    for kernel in os.listdir("."):
        if os.path.isfile(kernel):
            continue

        for file in os.listdir(kernel):
            if "iperf3" in file and file.split("-")[1] == "st" and not "bidir" in file:
                with open(f"{kernel}/{file}") as f:
                    print(f"Kernel {kernel} - {file}")
                    j = json.load(f)
                    if "udp" in file:
                        sender = j["end"]["sum_sent"]["bits_per_second"]
                        receiver = j["end"]["sum_received"]["bits_per_second"]
                        sender_reverse = j["end"]["sum_sent_bidir_reverse"]["bits_per_second"]
                        receiver_reverse = j["end"]["sum_received_bidir_reverse"]["bits_per_second"]
                        print(f"Sender: {sender}")
                        print(f"Sender reverse: {sender_reverse}")
                        print(f"Receiver: {receiver}")
                        print(f"Receiver reverse: {receiver_reverse}")
                    else:
                        sender = j["end"]["sum_sent"]["bits_per_second"]
                        receiver = j["end"]["sum_received"]["bits_per_second"]
                        sender_reverse = j["end"]["sum_sent_bidir_reverse"]["bits_per_second"]
                        receiver_reverse = j["end"]["sum_received_bidir_reverse"]["bits_per_second"]
                        print(f"Sender: {sender}")
                        print(f"Sender reverse: {sender_reverse}")
                        print(f"Receiver: {receiver}")
                        print(f"Receiver reverse: {receiver_reverse}")
                print('\n')







if __name__ == "__main__":
    main()