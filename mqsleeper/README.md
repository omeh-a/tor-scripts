# mqsleeper

UDP server which waits in the background to trigger the machinequeue script to die.

## Installation

This package is configured as a buildroot internal module. Put it in `.../buildroot/package/mqsleeper` and modify `.../buildroot/package/Config.in` to have a flag for this package.