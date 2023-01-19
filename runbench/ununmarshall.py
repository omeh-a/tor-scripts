import sys



def main():
    if len(sys.argv) != 2:
        print("Specify file")
        exit(0)

    with open(sys.argv[1], "r") as r, open(f"{sys.argv[1]}-clean", "w") as w:
        w.write("Requested_throughput,Achieved_throughput_sent,Achieved_throughput_received,Sent_size_received,Min,Avg,Max,Std-dev,Median")
        for line in r:
            if "[unmarshall]" in line:
                continue
            w.write(line)

if __name__ == "__main__":
    main()
