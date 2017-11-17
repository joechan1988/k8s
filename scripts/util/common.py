#!/usr/bin/python
# -*- coding: utf-8 -*-

import subprocess
import os

def shell_exec(cmd,shell=False,debug='',output=False):

    if not output:
        if debug != "1":
            subprocess.call(cmd,stdout=open(os.devnull, 'w'), \
                        stderr=subprocess.STDOUT,shell=shell)
        else:
            subprocess.call(cmd,shell=shell)

    else:
        if debug !="1":
            try:
                return subprocess.check_output(cmd,shell=shell,stderr=subprocess.STDOUT)
            except subprocess.CalledProcessError as ex:
                return "failed"
        else:
            try:
                return subprocess.check_output(cmd,shell=shell)
            except subprocess.CalledProcessError as ex:
                return "failed"




    #
    # if debug != "1":
    #     if not output:
    #         subprocess.call(cmd,stdout=open(os.devnull, 'w'),\
    #                     stderr=subprocess.STDOUT,shell=shell)
    #     else:
    #         try:
    #             return subprocess.check_output(cmd,shell=shell)
    #         except subprocess.CalledProcessError as ex:
    #             return "failed"
    #
    #
    # else:
    #     if not output:
    #         subprocess.call(cmd,shell=shell)
    #     else:
    #         try:
    #             return subprocess.check_output(cmd,shell=shell)
    #         except subprocess.CalledProcessError as ex:
    #             return "failed"

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

def check_preinstalled_binaries(bin_name):
    sys_path_str = os.environ["PATH"]
    sys_path = sys_path_str.split(':')
    for item in sys_path:
        if os.path.exists(os.path.join(item,bin_name)):
            return True

    return False

def disable_selinux():

    output = subprocess.check_output(["getenforce"])

    if 'Enforcing' in output:
        print('SELinux is Enabled.Disabling it')
        subprocess.call(["setenforce","0"])
        with open("/etc/selinux/config","r") as f:
            lines = f.readlines()
        with open("/etc/selinux/config","w") as f_w:
            for line in lines:
                if "SELINUX=enforcing" in line:
                    line = line.replace("enforcing","disabled")
                f_w.write(line)
