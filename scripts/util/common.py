#!/usr/bin/python
# -*- coding: utf-8 -*-

import subprocess
import os
from cfg import conf

def shell_exec(cmd,shell=False,debug=''):


    if debug != "1":
        subprocess.call(cmd,stdout=open(os.devnull, 'w'),\
                        stderr=subprocess.STDOUT,shell=shell)
    else:
        subprocess.call(cmd,shell=shell)