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

def check_binaries(bin_name):
    # sys_path_str = os.environ["PATH"]
    # sys_path = sys_path_str.split(':')
    # for item in sys_path:
    #     if os.path.exists(os.path.join(item,bin_name)):
    #         return True
    sys_path = '/usr/bin'
    bin_path = os.path.join(sys_path,bin_name)
    if os.path.exists(os.path.join(sys_path,bin_name)):
        return bin_path

    return None