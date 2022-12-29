# kernelmark

Automatic Linux kernel benchmarking targeting machines running PXE Linux. 

## Components

### Orchestration (main)

Main runtime - responsible for invoking everything else and managing failures (I expect lots of things to fail).

### Build

Responsible for invoking BuildRoot, feeding it appropriate config files and moving its output to a known location for the later steps.

### Deploy

Invoke machine queue scripts, make sure job lands at machine successfully.

### Test

Invoke testing scripts, collect and collate data.

### Finalise

Collect all test data to produce graphs, export it.