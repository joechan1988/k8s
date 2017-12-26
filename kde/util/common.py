#!/usr/bin/python
# -*- coding: utf-8 -*-
import logging
import subprocess
import os
import paramiko
import uuid
import urllib
from string import Template
from kde.templates import constants

import shutil

from scp import *


class RemoteShell(object):
    def __init__(self, ip='', user='', password=''):

        self.ip = ip
        self.user = user
        self.password = password
        self.instance = None
        self.debug = False

    def connect(self):

        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        # ssh.connect(self.ip, 22,
        #                 self.user,
        #                 self.password)
        try:
            ssh.connect(self.ip, 22,
                        self.user,
                        self.password)
        except:
            logging.error("Unable to connect %s", self.ip)
            return False

        self.instance = ssh

    def execute(self, cmd):

        stdin, stdout, stderr = self.instance.exec_command(cmd)
        out_ret = stdout.readlines()
        err_ret = stderr.readlines()

        if err_ret:
            return err_ret
        else:
            return out_ret

    def close(self):

        self.instance.close()

    def prep_dir(self, dir_name, clear=False):

        ret = self.execute("ls -l " + dir_name)

        logging.debug(ret)

        if "No such file" in ret[0]:
            self.execute("mkdir -p " + dir_name)

        elif clear == True:
            self.execute("rm -rf " + dir_name + "/*")

    def copy(self, local_path, remote_path):

        scpclient = SCPClient(self.instance.get_transport(), socket_timeout=15.0)
        try:
            scpclient.put(local_path, remote_path, recursive=True)
        except SCPException as e:
            logging.error(e.message)
            return

    def get(self,remote_path,local_path):

        scpclient = SCPClient(self.instance.get_transport(), socket_timeout=15.0)
        try:
            scpclient.get(remote_path, local_path, recursive=True)
        except SCPException as e:
            logging.error(e.message)
            return


def shell_exec(cmd, shell=False, debug=False, output=False):
    if not output:
        if not debug:
            subprocess.call(cmd, stdout=open(os.devnull, 'w'), \
                            stderr=subprocess.STDOUT, shell=shell)
        else:
            subprocess.call(cmd, shell=shell)

    else:
        if not debug:
            try:
                return subprocess.check_output(cmd, shell=shell, stderr=subprocess.STDOUT)
            except subprocess.CalledProcessError as ex:
                return "failed"
        else:
            try:
                return subprocess.check_output(cmd, shell=shell)
            except subprocess.CalledProcessError as ex:
                return "failed"


def shell_exec_remote(cmd, debug=False, ip='', user='', password=''):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(ip, 22,
                user,
                password)

    stdin, stdout, stderr = ssh.exec_command(cmd)
    # stdin,stdout,stderr = ssh.exec_command("env")

    out_ret = stdout.readlines()
    err_ret = stderr.readlines()

    ssh.close()
    if err_ret:
        return err_ret
    else:
        return out_ret


def copy_remote(local_path, remote_path, ip='', user='', password=''):
    pass


def check_binaries(path, bin_name):
    # sys_path_str = os.environ["PATH"]
    # sys_path = sys_path_str.split(':')
    # for item in sys_path:
    #     if os.path.exists(os.path.join(item,bin_name)):
    #         return True
    # sys_path = '/usr/bin'
    bin_path = os.path.join(path, bin_name)
    if os.path.exists(os.path.join(path, bin_name)):
        return bin_path

    return None


def download_binaries(urls, local_path="", default_path="/usr/bin/"):
    dir_name = str(uuid.uuid1())

    tmp_dir = "/tmp/" + dir_name + "/"

    prep_conf_dir(tmp_dir, '')

    for url in urls:
        file_name = url.split("/")[-1]
        file_tmp_path = tmp_dir + file_name
        dl_cmd = 'curl -o ' + file_tmp_path + ' -C - ' + url
        ch_cmd = 'chmod +x ' + file_tmp_path

        if local_path != "":
            mv_cmd = 'mv -f ' + file_tmp_path + ' ' + local_path
        else:
            mv_cmd = 'mv -f ' + file_tmp_path + ' ' + default_path

        shell_exec(dl_cmd, shell=True, debug=constants.debug)
        shell_exec(ch_cmd, shell=True, debug=constants.debug)
        shell_exec(mv_cmd, shell=True, debug=constants.debug)

    shell_exec('rm -rf ' + tmp_dir, shell=True)


def check_preinstalled_binaries(bin_name):
    sys_path_str = os.environ["PATH"]
    sys_path = sys_path_str.split(':')
    for item in sys_path:
        if os.path.exists(os.path.join(item, bin_name)):
            return True

    return False


def disable_selinux():
    output = subprocess.check_output(["getenforce"])

    if 'Enforcing' in output:
        print('SELinux is Enabled.Disabling it')
        subprocess.call(["setenforce", "0"])
        with open("/etc/selinux/config", "r") as f:
            lines = f.readlines()
        with open("/etc/selinux/config", "w") as f_w:
            for line in lines:
                if "SELINUX=enforcing" in line:
                    line = line.replace("enforcing", "disabled")
                f_w.write(line)


def render(src, dest, **kw):
    t = Template(open(src, 'r').read())
    if not os.path.exists(dest):
        os.mknod(dest)
    with open(dest, 'w') as f:
        f.write(t.substitute(**kw))
    logging.info("Generated configuration file: %s" % dest)


def prep_conf_dir(root, name, clear=False):
    absolute_path = os.path.join(root, name)
    if clear == True and os.path.exists(absolute_path):
        shutil.rmtree(absolute_path, ignore_errors=True)

    if not os.path.exists(absolute_path):
        os.makedirs(absolute_path)
    return absolute_path


def prep_dir_remote(root, name, clear=False, ip='', user='', password=''):
    absolute_path = os.path.join(root, name)

    rsh = RemoteShell(ip, user, password)
    rsh.connect()

    ret = rsh.execute("ls -l " + absolute_path)

    logging.info(ret)

    if "No such file" in ret[0]:
        rsh.execute("mkdir -p " + absolute_path)

    elif clear == True:
        rsh.execute("rm -rf " + absolute_path + "/*")

    rsh.close()


def arg(*args, **kwargs):
    """
    Arguments decorator for CLI args.

    :param args:
    :param kwargs:
    :return:
    """

    def _decorator(func):
        if not hasattr(func, 'arguments'):
            func.arguments = []
        if (args, kwargs) not in func.arguments:
            func.arguments.insert(0, (args, kwargs))

        return func

    return _decorator


def cmd_help(text):
    """
    Help decorator for CLI commands.

    :param text:
    :return:
    """

    def _decorator(func):
        if not hasattr(func, 'help'):
            func.help = text
        return func

    return _decorator


def get_log_level(log_level):
    level_group = {
        "debug": 10,
        "info": 20,
        "warning": 30,
        "error": 40,
        "critical": 50
    }
    return level_group[log_level.lower()]
