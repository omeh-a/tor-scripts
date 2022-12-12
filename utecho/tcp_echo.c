// Simple TCP echo - receives packets, and returns them.
// Matt Rossouw
// 07/12/2022

#include "utecho.h"
#define MAX_CLIENTS 100

void tcpEcho(int port, char buf[], int buf_size) {
    #ifdef DEBUG
        printf("Beginning TCP echo on port %d\n", port);
    #endif
    
    struct sockaddr_in sockAddr;
    socklen_t sockAddrLen;
    ssize_t msgLen;

    // Prepare socket address
    sockAddr.sin_family = AF_INET;
    sockAddr.sin_port = htons(port);
    sockAddr.sin_addr.s_addr = INADDR_ANY;

    // Create socket
    int sock = socket(AF_INET, SOCK_STREAM, IPPROTO_TCP);
    if (!sock) fail("Failed to create socket!");

    // Set buffer
    int bufsize = BUFFER_SIZE;
    setsockopt(sock, SOL_SOCKET, SO_RCVBUF, &bufsize, sizeof bufsize);

    // Try bind
    if (bind(sock, (struct sockaddr *)&sockAddr, sizeof sockAddr)) 
        fail("Failed to bind.");

    // Begin listen
    if(listen(sock, MAX_BACKLOG))
        fail("Failed to begin listening.");

    // Server loop
    for (;;) {
        sockAddrLen = sizeof sockAddr;
        size_t num_bytes = 0; // Size of received message

        // Accept next client
        int client = accept(sock, (struct sockaddr *)&sockAddr, &sockAddrLen);
        
        // Receive until client releases
        while ((num_bytes = recv(client, buf, BUFFER_SIZE, 0x0))) {
            #ifdef DEBUG
                // Get IP address as string
                struct sockaddr_in* ipv4 = (struct sockaddr_in*)&sockAddr;
                struct in_addr ip = ipv4->sin_addr;
                char ip_str[INET_ADDRSTRLEN];
                inet_ntop( AF_INET, &ip, ip_str, INET_ADDRSTRLEN );
                
                // Echo message content
                printf("%s : %.*s\n", ip_str, num_bytes, buf);
            #endif

            // Reply
            send(client, buf, num_bytes, 0x0);
        }

        // Terminate connection
        close(client);
    }
}