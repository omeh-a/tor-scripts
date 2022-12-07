// Combined TCP and UDP echo program.
// Matt Rossouw
// 07/12/2022

#include "utecho.h"

static void usage() {
    printf("USAGE: utecho [port] [mode]\n Modes: tcp, udp");
    exit(-1);
}

int main(int argc, const char *argv[]) {
    if (argc != 3) usage();
    int port = atoi(argv[1]);

    // Set mode
    int mode = 0;
    if (strcmp(argv[2], "tcp") == 0) {
        mode = MODE_TCP;
    } else if (strcmp(argv[2], "udp") == 0) {
        mode = MODE_UDP;
    } else {
        printf("Unknown socket mode \n");
        exit(0);
    }
    char buf[BUFFER_SIZE];
    
    switch (mode) {
        case MODE_TCP:
            tcpEcho(port, buf, BUFFER_SIZE);
            break;
        case MODE_UDP:
            udpEcho(port, buf, BUFFER_SIZE);
            break;
    }

    return 0;
}