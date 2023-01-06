# tor-scripts
Scripts for Linux Networking stuff

This repo contains most of the stuff for my ToR project.

## kernelmark

The main portion of this repo. Automated building and testing of Linux kernels, targeting PXELinux systems. See `/kernelmark/README.md`.

## runbench

Script invoking benchmarks using `ipbench`. Written by the maintainer of ipbench and my supervisor for this project, Peter Chubb.

## utecho

UDP / TCP echo.

This program listens to UDP or TDP given a port, simply echoing back packets it receives. 

UDP will simply bounce back everything, while TCP will wait on a client to close the connection before accepting a new client.
This entire folder is structured to be a buildroot external tree target.

## rootfs_overlay

Filesystem overlay which is copied over the generated one by buildroot. Contains:

### usr
* tester_wait_py - simple program to listen for kernelmark connection.
* ipbench - for benchmarking ip performance

### etc
* init scripts

## tester_wait

C version of tester_wait, in case it is neccesary to avoid using python on some machines.

## device_trees

Device trees for embedded devices.

## defconfigs

Kernel defconfigs for embedded devices.

## python2.7

Buildroot package for python2.7 - for testing.