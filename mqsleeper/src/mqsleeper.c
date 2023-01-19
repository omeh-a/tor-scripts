// mqsleeper.c
//    UDP server to trigger mq.sh shutdown
// Matt Rososuw (omeh-a)
// 01/23

#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <string.h>
#include <netinet/in.h>
#include <netinet/tcp.h>
#include <arpa/inet.h>
#include <time.h>

#define BUFFER_SIZE 5000

static void setbufsize(int sock, int size)
{
    setsockopt(sock, SOL_SOCKET, SO_RCVBUF, &size, sizeof size);
}

static void usage() {
    printf("USAGE: mqsleeper [port]\n");
    exit(-1);
}

int main(int argc, const char *argv[]) {
    if (argc != 2) usage();
    int port = atoi(argv[1]);

    char buf[BUFFER_SIZE];
    struct sockaddr_in sa;
    socklen_t sa_len;
    ssize_t msglen;
    sa.sin_family = AF_INET;
    sa.sin_port = htons(port);
    sa.sin_addr.s_addr = INADDR_ANY;
    int sock = socket(AF_INET, SOCK_DGRAM|SOCK_CLOEXEC, IPPROTO_UDP);
    setbufsize(sock, 2048*256);
    if (bind(sock, (struct sockaddr *)&sa, sizeof sa)) {
        printf("Failed to bind to socket!\n");
        exit(-1);
    }

    // receive one packet then print message and exit
    sa_len = sizeof sa;
    msglen = recvfrom(sock, buf, BUFFER_SIZE, 0, (struct sockaddr *)&sa, &sa_len);

    printf("\n\n\nOstritch\n\n\n");
    printf("Ostritch");

    exit(0);
}