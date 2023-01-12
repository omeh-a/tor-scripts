# logfile.py
#   Class wrapping around kernelmark's logging output
# Matt Rossouw (omeh-a)
# 01/23

import os

class logfile():
    def __init__(self):
        self.file = open("logfile", "a")
    
    def log(self, msg):
        self.file.write(msg)

Logfile = logfile()