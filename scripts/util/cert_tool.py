#!/usr/bin/python
# -*- coding: utf-8 -*-

import subprocess
import sys
import os
import common
import shutil
import argparse

# parser = argparse.ArgumentParser()
# parser.add_argument('--test',dest='test_unit',type=str,default='')
# args = parser.parse_args()


def check_cfssl():
    sys_path_str = os.environ["PATH"]
    sys_path = sys_path_str.split(':')
    for item in sys_path:
        if os.path.exists(os.path.join(item,'cfssl')):
            return True

    return False


def gen_ca_cert(ca_dir='',debug=''):

    if check_cfssl() != True:
        return

    shell_cmd ='cfssl gencert -initca '+ca_dir+'/ca-csr.json | cfssljson -bare ca'
    mv_cmd = 'mv -f ca.csr ca-key.pem ca.pem '+ca_dir

    common.shell_exec(shell_cmd,shell=True,debug=debug)
    common.shell_exec(mv_cmd,shell=True,debug=debug)
    # if debug == '1':
    #     subprocess.call(shell_cmd,shell=True)
    #     subprocess.call(mv_cmd,shell=True)
    # else:
    #     subprocess.call(shell_cmd, shell=True,stdout=open(os.devnull, 'w'),\
    #                     stderr=subprocess.STDOUT)
    #     subprocess.call(mv_cmd, shell=True,stdout=open(os.devnull, 'w'),\
    #                     stderr=subprocess.STDOUT)


def gen_cert_files(ca_dir='',profile='',csr_file='',cert_name='',dest_dir='',debug=''):

    if check_cfssl() != True:
        print('---Error: no cfssl tools installed---')
        return

    shell_cmd = 'cfssl gencert -ca=/etc/kubernetes/ssl/ca.pem \
                    -ca-key='+ca_dir+'/ca-key.pem \
                    -config='+ca_dir+'/ca-config.json \
                    -profile='+profile+' '+csr_file+' \
                        | cfssljson -bare '+cert_name
    # if debug=='1':
    #     subprocess.call(shell_cmd,shell=True)
    # else:
    #     subprocess.call(shell_cmd, shell=True,stdout = open(os.devnull, 'w'), \
    #              stderr = subprocess.STDOUT)
    common.shell_exec(shell_cmd,shell=True,debug=debug)
    if dest_dir:
        mv_cmd = 'mv -f '+cert_name+'.csr '\
                 +cert_name+'-key.pem ' \
                 +cert_name+'.pem '+dest_dir
        # subprocess.call(mv_cmd,shell=True)
        common.shell_exec(mv_cmd,shell=True,debug=debug)
