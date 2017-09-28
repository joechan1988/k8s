#!/usr/bin/python
# -*- coding: utf-8 -*-


from __future__ import print_function, unicode_literals  # We require Python 2.6 or later
from string import Template
import random
import string
import socket
import os
import sys
import argparse
import subprocess
import shutil
import base64
from io import open

if sys.version_info[:3][0] == 2:
    import ConfigParser as ConfigParser
    import StringIO as StringIO

if sys.version_info[:3][0] == 3:
    import configparser as ConfigParser
    import io as StringIO

#------Global Vars-----

base_dir = os.path.dirname(__file__)
FNULL = open(os.devnull,'w')

parser = argparse.ArgumentParser()

# --- args ---
parser.add_argument('--conf', dest='cfgfile', default=base_dir + '/k8s.cfg', type=str,
                    help="the path of Kubernetes configuration file")
parser.add_argument('--host-ip',dest='host_ip',type=str,help="Host IP Address")
parser.add_argument('--role',dest='node_role',type=str,default='',require=True,help="Node Role Type:master/minion")
parser.add_argument('--test',dest='test_unit',type=str,default='')
args = parser.parse_args()

# --- confs ---
conf = StringIO.StringIO()
conf.write("[configuration]\n")
conf.write(open(args.cfgfile).read())
conf.seek(0, os.SEEK_SET)
rcp = ConfigParser.RawConfigParser()
rcp.readfp(conf)

# --- vars ---
node_name = socket.gethostname()
if args.host_ip:
    node_ip= args.host_ip
else:
    node_ip = rcp.get("configuration", "node_ip")



#     ----config dest folders----

template_dir = os.path.join(base_dir,"templates")
systemd_dir = "/etc/systemd/system/"
etcd_ssl_dir = "/etc/etcd/ssl/"
k8s_ssl_dir = "/etc/kubernetes/ssl/"


#------ Functions: Utilities ------

def prep_conf_dir(root, name):
    absolute_path = os.path.join(root, name)
    if not os.path.exists(absolute_path):
        os.makedirs(absolute_path)
    return absolute_path

def render(src, dest, **kw):
    t = Template(open(src, 'r').read())
    if not os.path.exists(dest):
        os.mknod(dest)
    with open(dest, 'w') as f:
        f.write(t.substitute(**kw))
    print("Generated configuration file: %s" % dest)

def get_binaries():
    subprocess.call(["bash", "-c", "./get-binaries.sh"])

def generate_cert():

    render(os.path.join(template_dir,"etcd-csr.json"),
           os.path.join(etcd_ssl_dir,"etcd-csr.json"),
           node_name=node_name,
           node_ip=node_ip)

    subprocess.call(["bash","-c", os.path.join(base_dir,"util","generate_cert.sh")])

def get_cert_from_master():
    pass


#------ Functions: Deployment Actions ------
def deploy_etcd():

    prep_conf_dir("/var/lib/etcd",'')
    discovery = subprocess.check_output(["curl", "-s", "https://discovery.etcd.io/new?size=1"])

    render(os.path.join(template_dir,"etcd.service"),
           os.path.join(systemd_dir,"etcd.service"),
           node_ip=node_ip,
           node_name=node_name,
           discovery=discovery.replace('https','http'))

def deploy_flannel():
    print('------Deploying Flannel------')

def deploy_kubelet():
    print('------Deploying kubelet------')

def deploy_apiserver():
    print('------Deploying kube-apiserver ------')

def deploy_controller_manager():
    print('------Deploying kube-controller-manager ------')

def deploy_scheduler():
    print('------Deploying kube-scheduler ------')

def deploy_addons():
    print('------Deploying Addons:kube-dns ------')


#------ Deployment Start ------

role = args.node_role

if args.test_unit:
    print('------Script Testing------')
else:
    prep_conf_dir(etcd_ssl_dir,'')
    prep_conf_dir(k8s_ssl_dir,'')
    get_binaries()
    generate_cert()


    if role == 'master':
        deploy_etcd()
        deploy_flannel()
        deploy_kubelet()
        deploy_apiserver()
        deploy_controller_manager()
        deploy_scheduler()
        deploy_addons()

        subprocess.call(["systemctl", "daemon-reload"])
        subprocess.call(["systemctl", "start", "etcd"])
        subprocess.call(["systemctl", "restart", "docker"])
        subprocess.call(["systemctl", "start", "flanneld"])
        subprocess.call(["systemctl", "start", "kubelet"])
        subprocess.call(["systemctl", "start", "kube-apiserver"])
        subprocess.call(["systemctl", "start", "kube-controller-manager"])
        subprocess.call(["systemctl", "start", "kube-scheduler"])
        # subprocess.call(["systemctl", "start", ""])

    if role == 'minion':
        get_cert_from_master()

    # ------ Start Service ------














