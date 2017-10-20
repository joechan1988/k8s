#!/usr/bin/python
# -*- coding: utf-8 -*-

import subprocess
import os

def shell_exec(cmd,shell=False,debug='',output=False):


    if debug != "1":
        if not output:
            subprocess.call(cmd,stdout=open(os.devnull, 'w'),\
                        stderr=subprocess.STDOUT,shell=shell)
        else:
            try:
                return subprocess.check_output(cmd,shell=shell,stdout=open(os.devnull, 'w'), \
                                           stderr=subprocess.STDOUT)
            except subprocess.CalledProcessError as ex:
                return "failed"


    else:
        if not output:
            subprocess.call(cmd,shell=shell)
        else:
            try:
                return subprocess.check_output(cmd,shell=shell)
            except subprocess.CalledProcessError as ex:
                return "failed"

def check_binaries(path,bin_name):
    # sys_path_str = os.environ["PATH"]
    # sys_path = sys_path_str.split(':')
    # for item in sys_path:
    #     if os.path.exists(os.path.join(item,bin_name)):
    #         return True
    # sys_path = '/usr/bin'
    bin_path = os.path.join(path,bin_name)
    if os.path.exists(os.path.join(path,bin_name)):
        return bin_path

    return None