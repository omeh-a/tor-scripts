# machine.py
#   Class representing a target machine.
# Matt Rossouw (omeh-a)
# 12/2022

class Machine():
    def __init__(self, name, manifest):
        self.name = name
        self.ip = manifest["ip"]
        self.isa = manifest["isa"]
        self.soc = manifest["soc"]
        self.kernel_defconfig = manifest["kernel_defconfig"]
        self.dev_tree = manifest["device_tree"]
        self.mac = manifest["mac"]
        self.forward = manifest["forward"]
        self.logical_cpus = manifest["logical_cpus"]
