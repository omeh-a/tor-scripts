# testerwait
#   Simple program which waits for a UDP packet then continues. Used to
#   allow the test section of kernelmark to wait until the machine is ready
#   post-boot.
#
# Matt Rossouw (omeh-a)
# 01/23


import os
import socket
import time


def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((str(socket.INADDR_ANY), 1345))

    buff_sz = 1000
    client = sock.recvfrom(buff_sz)[1]

    sock.sendto(str.encode("Emu"), client)
    sock.close()
    exit(0)


if __name__ == "__main__":
    main()