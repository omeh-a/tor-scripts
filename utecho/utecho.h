#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <string.h>
#include <netinet/in.h>
#include <netinet/tcp.h>

#define DEBUG 1
#define BUFFER_SIZE 5000
#define MAX_BACKLOG 50
#define MODE_UDP 0
#define MODE_TCP 1

void udpEcho(int port, char buf[], int buf_size);
void tcpEcho(int port, char buf[], int buf_size);

static void fail(const char* msg) {
    perror(msg);
    exit(-1);
}