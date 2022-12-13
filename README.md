# tor-scripts
Scripts for Linux Networking stuff

This repo contains most of the stuff for my ToR project. This entire folder is structured to be a buildroot external tree target.

## utecho
UDP / TCP echo.

This program listens to UDP or TDP given a port, simply echoing back packets it receives. 

UDP will simply bounce back everything, while TCP will wait on a client to close the connection before accepting a new client.
