#!/usr/bin/python
# -*- coding: utf-8 -*-

import subprocess
import sys
import os
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

def gen_ca_cert(ca_dir=''):

    checkcfssl = check_cfssl()
    if check_cfssl() != True:
        return

    shell_cmd ='cfssl gencert -initca '+ca_dir+'/ca-csr.json | cfssljson -bare ca'
    mv_cmd = 'mv -f ca.csr ca-key.pem ca.pem '+ca_dir

    subprocess.call(shell_cmd,shell=True)
    # shutil.move('ca.csr',ca_dir)
    subprocess.call(mv_cmd,shell=True)


def gen_cert_files(ca_dir='',profile='',csr_file='',cert_name='',dest_dir=''):

    checkcfssl = check_cfssl()
    if check_cfssl() != True:
        print('---Error: no cfssl tools installed---')
        return
    #
    # shell_cmd = ['cfssl','gencert','-ca='+ca_dir+'/ca.pem',\
    #              '-ca-key='+ca_dir+'/ca-key.pem',\
    #              '-config='+ca_dir+'ca-config.json', \
    #              '-profile='+profile,csr_file ]
    shell_cmd = 'cfssl gencert -ca=/etc/kubernetes/ssl/ca.pem \
                    -ca-key='+ca_dir+'/ca-key.pem \
                    -config='+ca_dir+'/ca-config.json \
                    -profile='+profile+' '+csr_file+' \
                        | cfssljson -bare '+cert_name
    subprocess.call(shell_cmd,shell=True)

    if dest_dir:
        mv_cmd = 'mv -f '+cert_name+'.csr '\
                 +cert_name+'-key.pem ' \
                 +cert_name+'.pem '+dest_dir
        subprocess.call(mv_cmd,shell=True)

# if args.test_unit :
# print ('----Unit Testing')
# gen_cert_files(ca_dir='/etc/kubernetes/ssl',profile='kubernetes',\
#                csr_file='/etc/etcd/ssl/etcd-csr.json',cert_name='etcd',\
#                dest_dir='/etc/etcd/ssl/')
# gen_ca_cert(ca_dir='/etc/kubernetes/ssl')
# sys.exit(0)