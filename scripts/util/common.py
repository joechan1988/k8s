#!/usr/bin/python
# -*- coding: utf-8 -*-
import logging
import subprocess
import os
import paramiko
from string import Template

import shutil


def shell_exec(cmd,shell=False,debug=False,output=False):

    if not output:
        if not debug:
            subprocess.call(cmd,stdout=open(os.devnull, 'w'), \
                        stderr=subprocess.STDOUT,shell=shell)
        else:
            subprocess.call(cmd,shell=shell)

    else:
        if not debug:
            try:
                return subprocess.check_output(cmd,shell=shell,stderr=subprocess.STDOUT)
            except subprocess.CalledProcessError as ex:
                return "failed"
        else:
            try:
                return subprocess.check_output(cmd,shell=shell)
            except subprocess.CalledProcessError as ex:
                return "failed"

def remote_exec(cmd,debug=False,ip='',user='',password=''):

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(ip,22,
                user,
                password)

    stdin,stdout,stderr = ssh.exec_command(cmd)
    # stdin,stdout,stderr = ssh.exec_command("env")


    out_ret = stdout.readlines()
    err_ret = stderr.readlines()

    ssh.close()
    if err_ret:
        return err_ret
    else:
        return out_ret


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


def render(src, dest, **kw):
    t = Template(open(src, 'r').read())
    if not os.path.exists(dest):
        os.mknod(dest)
    with open(dest, 'w') as f:
        f.write(t.substitute(**kw))
    print("Generated configuration file: %s" % dest)

def prep_conf_dir(root, name,clear=False):
    absolute_path = os.path.join(root, name)
    if clear == True and os.path.exists(absolute_path):
        shutil.rmtree(absolute_path,ignore_errors=True)

    if not os.path.exists(absolute_path):
        os.makedirs(absolute_path)
    return absolute_path