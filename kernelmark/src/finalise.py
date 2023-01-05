# finalise
#   Script to collect and collate test results, generate graphs.
# Matt Rossouw (omeh-a)
# 01/23

import matplotlib.pyplot as plt
import json
import os

def finalise(out_dir, machine_name):
    results = {}
    
    # Find all tests
    for kernels in os.listdir(f"{out_dir}/{machine_name}"):
        






# For testing
if __name__ == "__main__":
    finalise("~/tor-scripts/kernelmark/output", "haswell3")
