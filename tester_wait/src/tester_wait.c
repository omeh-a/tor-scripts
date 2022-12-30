// wait.c
// Program to hold until kernelmark attaches to it.
// Matt Rossouw (omeh-a)
// 12/2022

#include <stdio.h>
#include <stdlib.h>
#include <netinet/tcp.h>
#include <arpa/inet.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <string.h>

#define PORT 1345

int main(int argc, char* argv[]) {
    
    printf("Waiting for connection on port %d\n", PORT);
    // Listen on UDP on PORT
    struct sockaddr_in sa;
    socklen_t sa_len;
    ssize_t msglen;
    sa.sin_family = AF_INET;
    sa.sin_port = htons(PORT);
    sa.sin_addr.s_addr = INADDR_ANY;
    int sock = socket(AF_INET, SOCK_DGRAM|SOCK_CLOEXEC, IPPROTO_UDP);
    if (bind(sock, (struct sockaddr *)&sa, sizeof sa)) {
        exit(-1);
    }

    sa_len = sizeof sa;
    msglen = recvfrom(sock, NULL, 0, 0, (struct sockaddr *)&sa, &sa_len);
    char buf[6] = "READY\0";
    sendto(sock, buf, 6, 0, (struct sockaddr *)&sa, sa_len);

    printf("Connection received, exiting.\n");
    return 0;
}