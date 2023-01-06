# kernelmark

Automatic Linux kernel benchmarking targeting machines running PXE Linux.

## Usage

`python3 kernelmark [machine] [kernels.json] [flags]`

Flags"
* `clean` - erase builds and results for selected machine.
* `hardclean` - erase builds and results for all machines.
* `skipdone` - don't attempt to test builds which have an existing test file.
* `buildonly` - don't deploy or test kernels. Just build.

### Input files

Kernels must be supplied in a json file of the format
```
{
    major_version: [minor, minor, minor ...],
    next_major: [minor ...]
}
```

### Configuration

There are two configuration files which must be supplied:
* `/conf/build.json` - this sets the location of buildroot as well as the desired output directory, and location of BR config templates.
* `/conf/machines.json` - this file is a manifest containing machines known to the program. Put your machine here to use it.

There are a few other configuration files which you may need to tinker with too, but these are supplied:
* `src/kernel_headers` and `src/kernel_headers_atleast` - these are just dumps of Buildroot parameters which need to be used to generate .configs. If newer headers come out, they need to be added to these lists.
* `/br_configs/` - contains buildroot templates for machines. Kernelmark will select `[machine].config` always. These files can be grabbed directly from buildroot (after configuring with `make menuconfig`) provided they are run through `sanitise.py` in that directory.  

## Components

### Orchestration (main)

Main runtime - responsible for invoking everything else and managing failures (I expect lots of things to fail).

### Build

Responsible for invoking BuildRoot, feeding it appropriate config files and moving its output to a known location for the later steps.

### Deploy

Invoke machine deployment scripts, make sure job lands at machine successfully. If you want to use this you will need to fully replace this module to boot your own PXE Linux system or emulator.

### Test

Invoke testing scripts, collect and collate data.

### Finalise

Collect all test data to produce graphs, export it.