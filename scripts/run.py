#!/usr/bin/python
# -*- coding: utf-8 -*-


from __future__ import print_function, unicode_literals  # We require Python 2.6 or later
from string import Template
import socket
import json
import os
import logging
import sys
import argparse
import subprocess
import shutil
import paramiko
import time
from templates import json_schema
from util import cert_tool
from util import cfg
from util import common
from util import config_parser
from scp import SCPClient
from io import open


logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
                    datefmt='%a, %d %b %Y %H:%M:%S',
                    )


#------Global Vars-----

base_dir = os.path.dirname(__file__)
# FNULL = open(os.devnull,'w')
cfg_file = base_dir+'/k8s.cfg'


master_service_list = ['kube-apiserver',
                       'kube-controller-manager','kube-scheduler']
node_service_list = ['docker','kubelet','kube-proxy']
success_list =[]
failed_list = []

def test():
    # if not common.check_preinstalled_binaries("docker") \
    #         or not common.check_preinstalled_binaries("docker-current"):
    #     print("FATAL:  Docker is NOT installed")
    # exit(2)
    #
    # configs = config_parser.Config("./cluster.yml")
    # configs.load()
    # print(configs.data.get('nodes')[0].get('role'))

    cmd = '''
        sysctl
    '''
    #
    # cmd = 'env'
    logging.debug(cmd)
    ret = common.shell_exec_remote(cmd, ip='192.168.1.199', user='root', password='123456')

    print(ret)


def main():

    parser = argparse.ArgumentParser()
    parser.add_argument('--test',dest='test_unit',type=str,default='')
    subparsers = parser.add_subparsers(help='Commands')

    parser_generate_cert = subparsers.add_parser('generate_cert', help='Generate Cert')
    # parser_generate_cert.set_defaults(func=generate_cert)

    parser_deploy = subparsers.add_parser('deploy',help='Deploy Kubernetes')
    # parser_deploy.set_defaults(func=deploy)

    parser_test = subparsers.add_parser('test',help='Run Tests')
    parser_test.set_defaults(func=test)

    parser_test = subparsers.add_parser('get_binaries',help='Run Tests')
    # parser_test.set_defaults(func=get_binaries)

    args = parser.parse_args()
    args.func()


if __name__ == "__main__":
    main()