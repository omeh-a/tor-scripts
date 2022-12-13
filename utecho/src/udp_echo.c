// UDP echo, just Peter's program modified to fit utecho.
// Matt Rossouw
// 07/12/2022

#include "utecho.h"

static void setbufsize(int sock, int size)
{
    setsockopt(sock, SOL_SOCKET, SO_RCVBUF, &size, sizeof size);
}

void udpEcho(int port, char buf[], int buf_size)
{

    #ifdef DEBUG
        printf("Beginning UDP echo on port %d\n", port);
    #endif

    struct sockaddr_in sa;
    socklen_t sa_len;
    ssize_t msglen;
    sa.sin_family = AF_INET;
    sa.sin_port = htons(port);
    sa.sin_addr.s_addr = INADDR_ANY;
    int sock = socket(AF_INET, SOCK_DGRAM|SOCK_CLOEXEC, IPPROTO_UDP);
    setbufsize(sock, 2048*256);
    if (bind(sock, (struct sockaddr *)&sa, sizeof sa)) {
        fail("bind failure");
    }

    for (;;) { 
        sa_len = sizeof sa;
        msglen = recvfrom(sock, buf, BUFFER_SIZE, 0, (struct sockaddr *)&sa, &sa_len);
        
        #ifdef DEBUG
            printf("msg: %s\n", buf);
        #endif
        
        sendto(sock, buf, msglen, 0, (struct sockaddr *)&sa, sa_len);
    }
}