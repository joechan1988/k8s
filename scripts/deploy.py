#!/usr/bin/python
# -*- coding: utf-8 -*-


from __future__ import print_function, unicode_literals  # We require Python 2.6 or later
from string import Template
import socket
import os
import sys
import argparse
import subprocess
import shutil
import paramiko
from io import open

if sys.version_info[:3][0] == 2:
    import ConfigParser as ConfigParser
    import StringIO as StringIO

if sys.version_info[:3][0] == 3:
    import configparser as ConfigParser
    import io as StringIO

#------Global Vars-----

base_dir = os.path.dirname(__file__)
# FNULL = open(os.devnull,'w')

parser = argparse.ArgumentParser()

master_service_list = ['etcd','kube-apiserver',
                'kube-controller-manager','kube-scheduler']
node_service_list = ['flanneld','docker','kubelet','kube-proxy']
success_list =[]
failed_list = []

# --- args ---
parser.add_argument('--conf', dest='cfgfile', default=base_dir + '/k8s.cfg', type=str,
                    help="the path of Kubernetes configuration file")
parser.add_argument('--host-ip',dest='host_ip',type=str,help="Host IP Address")
parser.add_argument('--role',dest='node_role',type=str,default='',required=True,help="Node Role Type:master/minion")
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

debug = rcp.get("configuration", "debug")
k8s_version = rcp.get("configuration", "k8s_version")

node_name = socket.gethostname()
if args.host_ip:
    node_ip= args.host_ip
else:
    node_ip = rcp.get("configuration", "node_ip")

master_ip = rcp.get("configuration", "master_ip")
kube_apiserver = "https://"+master_ip+":6443"
cluster_kubernetes_svc_ip = rcp.get("configuration", "cluster_kubernetes_svc_ip")
cluster_dns_domain = rcp.get("configuration", "cluster_dns_domain")
cluster_dns_svc_ip =rcp.get("configuration", "cluster_dns_svc_ip")
node_port_range =rcp.get("configuration", "node_port_range")
cluster_cidr =rcp.get("configuration", "cluster_cidr")
service_cidr =rcp.get("configuration", "service_cidr")

etcd_endpoints="https://"+master_ip+":2379"

flannel_etcd_prefix = "/kubernetes/network"
bootstrap_token=  rcp.get("configuration", "bootstrap_token")

#     ----config dest folders----

template_dir = os.path.join(base_dir,"templates")
systemd_dir = "/etc/systemd/system/"
etcd_ssl_dir = "/etc/etcd/ssl/"
k8s_ssl_dir = "/etc/kubernetes/ssl/"


#------ Functions: Utilities ------

def shell_exec(cmd,shell=False):
    if debug != "1":
        subprocess.call(cmd,stdout=open(os.devnull, 'w'),\
                        stderr=subprocess.STDOUT,shell=shell)
    else:
        subprocess.call(cmd,shell=shell)

def prep_conf_dir(root, name,clear=False):
    absolute_path = os.path.join(root, name)
    if clear == True and os.path.exists(absolute_path):
        shutil.rmtree(absolute_path,ignore_errors=True)

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
    # subprocess.call([os.path.join(base_dir,'get-binaries.sh'),k8s_version])
    shell_cmd = [os.path.join(base_dir,'get-binaries.sh'),k8s_version]
    shell_exec(shell_cmd)

def generate_cert():

    prep_conf_dir(etcd_ssl_dir,'',clear=True)
    prep_conf_dir('/etc/kubernetes','',clear=True)
    prep_conf_dir(k8s_ssl_dir,'',clear=True)

    render(os.path.join(template_dir,"etcd-csr.json"),
           os.path.join(etcd_ssl_dir,"etcd-csr.json"),
           node_name=node_name,
           node_ip=node_ip)
    render(os.path.join(template_dir,"kubernetes-csr.json"),
           os.path.join(k8s_ssl_dir,"kubernetes-csr.json"),
           node_name=node_name,
           node_ip=node_ip,
           master_ip=master_ip,
           cluster_kubernetes_svc_ip=cluster_kubernetes_svc_ip)
    render(os.path.join(template_dir,"token.csv"),
           os.path.join("/etc/kubernetes/","token.csv"),
           bootstrap_token=bootstrap_token)
    render(os.path.join(template_dir, "admin-csr.json"),
           os.path.join(k8s_ssl_dir, "admin-csr.json"))
    render(os.path.join(template_dir, "kube-proxy-csr.json"),
           os.path.join(k8s_ssl_dir, "kube-proxy-csr.json"))

    shell_cmd = [os.path.join(base_dir,"util","generate_cert.sh")]
    shell_exec(shell_cmd)
    # subprocess.call(os.path.join(base_dir,"util","generate_cert.sh"))

def generate_kubeconfig():
    # subprocess.call([os.path.join(base_dir, "util", "generate_kubeconfig.sh"), \
    #                  kube_apiserver, bootstrap_token])
    shell_cmd = [os.path.join(base_dir, "util", "generate_kubeconfig.sh"), \
                     kube_apiserver, bootstrap_token]
    shell_exec(shell_cmd)

def get_cert_from_master():

    prep_conf_dir('/etc/flanneld/ssl','',clear=True)
    prep_conf_dir(k8s_ssl_dir,'',clear=True)

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(master_ip,22,'root','123456')
    sftp = paramiko.SFTPClient.from_transport(ssh.get_transport())
    # sftp = ssh.open_sftp()
    sftp.get('/etc/kubernetes/*','/etc/kubernetes')



#------ Functions: Deployment Actions ------
def config_etcd():
    print('------Configurating Etcd------')
    prep_conf_dir("/var/lib/etcd",'',clear=True)
    while True:
        discovery = subprocess.check_output(["curl", "-s", "https://discovery.etcd.io/new?size=1"])
        if "etcd.io" in discovery:
            break

    render(os.path.join(template_dir,"etcd.service"),
           os.path.join(systemd_dir,"etcd.service"),
           node_ip=node_ip,
           node_name=node_name,
           discovery=discovery.replace('https','http'))

def config_flannel():
    print('------Configurating Flannel------')

    render(os.path.join(template_dir,"flanneld.service"),
           os.path.join(systemd_dir, "flanneld.service"),
           master_ip=master_ip)

    render(os.path.join(template_dir,"docker.service"),
           os.path.join(systemd_dir, "docker.service"))


def config_kubelet():
    print('------Configurating kubelet------')

    prep_conf_dir("/var/lib/kubelet",'',clear=True)
    render(os.path.join(template_dir,"kubelet.service"),
           os.path.join(systemd_dir, "kubelet.service"),
           node_ip=node_ip,
           cluster_dns_svc_ip=cluster_dns_svc_ip,
           cluster_dns_domain=cluster_dns_domain)

def config_apiserver():
    print('------Configurating kube-apiserver ------')

    render(os.path.join(template_dir,"kube-apiserver.service"),
           os.path.join(systemd_dir, "kube-apiserver.service"),
           master_ip=master_ip,
           service_cidr=service_cidr,
           node_port_range=node_port_range,
           )

def config_controller_manager():
    print('------Configurating kube-controller-manager ------')

    render(os.path.join(template_dir,"kube-controller-manager.service"),
           os.path.join(systemd_dir, "kube-controller-manager.service"),
           master_ip=master_ip,
           service_cidr=service_cidr,
           cluster_cidr=cluster_cidr
           )

def config_scheduler():
    print('------Configurating kube-scheduler ------')
    render(os.path.join(template_dir,"kube-scheduler.service"),
           os.path.join(systemd_dir, "kube-scheduler.service"),
           master_ip=master_ip,
           service_cidr=service_cidr,
           cluster_cidr=cluster_cidr
           )

def config_proxy():
    print('------Configurating kube-proxy ------')

    prep_conf_dir("/var/lib/kube-proxy",'',clear=True)
    render(os.path.join(template_dir, "kube-proxy.service"),
           os.path.join(systemd_dir, "kube-proxy.service"),
           node_ip=node_ip,
           service_cidr=service_cidr,
           )


def create_csr_auto_approve():
    print('------Configurating CSR Auto Approve ------')
    # subprocess.call(["kubectl","create","clusterrolebinding","kubelet-bootstrap",\
    #                  "--clusterrole=system:node-bootstrapper","--user=kubelet-bootstrap"])
    # subprocess.call(["kubectl","create","-f","../addons/csr-auto-approve.yml"])

    # rbac_cmd = "kubectl create clusterrolebinding kubelet-bootstrap --clusterrole=system:node-bootstrapper --user=kubelet-bootstrap"
    csr_cmd = "kubectl create -f ../addons/csr-auto-approve.yml"
    # shell_exec(rbac_cmd)
    shell_exec(csr_cmd,shell=True)

def label_master_node():

    # subprocess.call(["kubectl","label","node",node_ip,"node-role.kubernetes.io/master="])
    # subprocess.call(["kubectl","label","node",node_ip,"kubeadm.alpha.kubernetes.io/role=master"])
    shell_cmd = "kubectl label node "+node_ip+" node-role.kubernetes.io/master="
    shell_exec(shell_cmd,shell=True)

def initiate_flanneld():
    # subprocess.call([os.path.join(base_dir, "util", "initiate_flannel.sh"), \
    #                  etcd_endpoints, flannel_etcd_prefix, cluster_cidr])
    print("------Initiating Flannel------")
    shell_cmd = [os.path.join(base_dir, "util", "initiate_flannel.sh"),etcd_endpoints, flannel_etcd_prefix, cluster_cidr]
    shell_exec(shell_cmd,shell=False)

def start_service(service_name):
    print("------Starting Service: %s"% service_name)
    output = subprocess.check_output(["systemctl","restart",service_name])

    if 'failed' in output:
        failed_list.append(service_name)
    else:
        success_list.append(service_name)

#------ Deployment Start ------

role = args.node_role

if args.test_unit:
    print('------Script Testing------')
    prep_conf_dir('/var/lib/kubelet','',clear=True)
    sys.exit(0)
else:
    get_binaries()



    if role == 'master':
        generate_cert()
        generate_kubeconfig()

        config_etcd()
        config_flannel()
        config_apiserver()
        config_controller_manager()
        config_scheduler()
        config_proxy()
        config_kubelet()

        subprocess.call(["systemctl", "daemon-reload"])
        #
        # print("Starting Etcd...")
        # subprocess.call(["systemctl", "start", "etcd"])
        # print("Starting Flannel...")
        # subprocess.call(["systemctl", "start", "flanneld"])
        # print("Starting Docker...")
        # subprocess.call(["systemctl", "restart", "docker"])
        # print("Starting kube-apiserver...")
        # subprocess.call(["systemctl", "start", "kube-apiserver"])
        # print("Starting kube-controller-manager...")
        # subprocess.call(["systemctl", "start", "kube-controller-manager"])
        # print("Starting kube-scheduler...")
        # subprocess.call(["systemctl", "start", "kube-scheduler"])
        # print("Starting kubelet...")
        # subprocess.call(["systemctl", "start", "kubelet"])
        # # subprocess.call(["systemctl", "start", ""])

    if role == 'minion':
        get_cert_from_master()

#------Start Service -------

if args.node_role == 'master':

    #---Start Master Components---
    for service in master_service_list:
        start_service(service)
    # subprocess.call(["kubectl", "apply", "-f", "../addons/csr-auto-approve.yml"])
    create_csr_auto_approve()
    #---initiate flannel etcd-data -----
    initiate_flanneld()
    #---Start K8s Node Components---
    for service in node_service_list:
        start_service(service)

    print('Successfully Start Service: %s' % success_list)
    print('Failed to Start: %s' % failed_list)

    if 'kube-apiserver' in success_list \
        and 'kube-controller-manager' in success_list \
        and 'kubelet' in success_list:
        while True:
            check_node = subprocess.check_output(["kubectl","get","node"])
            if node_ip in check_node:
                label_master_node()
                break

else:
    for service in node_service_list:
        start_service(service)

    print('Successfully Start Service: %s' % success_list)
    print('Failed to Start: %s' % failed_list)













