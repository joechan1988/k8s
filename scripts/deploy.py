#!/usr/bin/python
# -*- coding: utf-8 -*-


from __future__ import print_function, unicode_literals  # We require Python 2.6 or later
from string import Template
import socket
import json
import os
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
from scp import SCPClient
from io import open


#------Global Vars-----

base_dir = os.path.dirname(__file__)
# FNULL = open(os.devnull,'w')
cfg_file = base_dir+'/k8s.cfg'


master_service_list = ['kube-apiserver',
                'kube-controller-manager','kube-scheduler']
node_service_list = ['flanneld','docker','kubelet','kube-proxy']
success_list =[]
failed_list = []

# --- confs ---

configs = cfg.conf(cfg_file)
configs.load_all_config()

# --- vars ---
node_ip =configs.node_ip
node_name= socket.gethostname()

kube_apiserver = "https://"+node_ip+":6443"
etcd_endpoints="https://"+configs.master_ip+":2379"

#     ----config dest folders----

template_dir = os.path.join(base_dir,"templates")
systemd_dir = "/etc/systemd/system/"
etcd_ssl_dir = "/etc/etcd/ssl/"
k8s_ssl_dir = "/etc/kubernetes/ssl/"


#------ Functions: Utilities ------

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

def copy_binaries():

    print('------Copying Binaries to System Executables Directory------')
    parent_folder = os.path.abspath(os.path.join(base_dir,os.path.pardir))
    bin_folder = os.path.join(parent_folder,"bin")

    copy_cmd = ["cp","-f",bin_folder+"/*","/usr/bin"]
    common.shell_exec(cmd=copy_cmd,debug=configs.debug)


def get_binaries():
    # subprocess.call([os.path.join(base_dir,'get-binaries.sh'),k8s_version])
    # shell_cmd = [os.path.join(base_dir,'util','get-binaries.sh'),
    #              configs.k8s_version,
    #              configs.update_binaries]
    # common.shell_exec(shell_cmd,debug=configs.debug)
    print('------Preparing Required Binaries------')
    util_bin_list = ["cfssl","cfssl-certinfo","cfssljson"]
    k8s_bin_list = ["kubectl",
                    "kubelet","kube-apiserver","kube-scheduler",
                    "kube-controller-manager","kube-proxy","kubeadm",
                    "etcd","etcdctl","flanneld","mk-docker-opts.sh",
                    "cfssl","cfssl-certinfo","cfssljson"]
    # etcd_bin_list = ["etcd","etcdctl"]
    # flannel_bin_list = ["flanneld","mk-docker-opts.sh"]

    base_url=configs.binaries_download_url

    parent_dir = os.path.abspath(os.path.join(base_dir,os.path.pardir))
    bin_dir = os.path.join(parent_dir,"bin")
    sys_bin_dir = '/usr/bin/'

    common.shell_exec('chmod +x '+bin_dir+'/*',shell=True,debug=configs.debug)

    for bin in k8s_bin_list:
        bin_path = common.check_binaries(bin_dir,bin)
        sys_bin_path = common.check_binaries(sys_bin_dir,bin)
        download_cmd = 'wget -c -P /usr/bin/ ' + \
                    base_url +'binaries/' + configs.k8s_version + '/server/bin/' + bin
        cp_cmd = ["cp","-f",bin_dir+"/"+bin,"/usr/bin"]
        if not bin_path:
            if not sys_bin_path:
                common.shell_exec(download_cmd,shell=True,debug=configs.debug)
                bin_path = common.check_binaries(sys_bin_dir,bin)
                common.shell_exec('chmod +x '+bin_path,shell=True,debug=configs.debug)
            elif configs.update_binaries == 'yes':
                common.shell_exec('rm -f '+bin_path, shell=True,debug=configs.debug)
                common.shell_exec(download_cmd,shell=True,debug=configs.debug)
                bin_path = common.check_binaries(sys_bin_dir,bin)
                common.shell_exec('chmod +x '+bin_path,shell=True,debug=configs.debug)
        else:
            if not sys_bin_path:
                common.shell_exec(cp_cmd,debug=configs.debug)
                # bin_path = common.check_binaries(sys_bin_dir,bin)
                # common.shell_exec('chmod +x '+bin_path,shell=True,debug=configs.debug)
            elif configs.update_binaries == 'yes':
                common.shell_exec('rm -f '+bin_path, shell=True,debug=configs.debug)
                common.shell_exec(cp_cmd,debug=configs.debug)
                # bin_path = common.check_binaries(sys_bin_dir,bin)
                # common.shell_exec('chmod +x '+bin_path,shell=True,debug=configs.debug)


    # for bin in etcd_bin_list:
    #     bin_path = common.check_binaries(bin)
    #     download_cmd = 'wget -c -P /usr/bin/ ' + \
    #                 base_url + 'etcd/' + bin
    #     if not bin_path:
    #         common.shell_exec(download_cmd,shell=True,debug=configs.debug)
    #         bin_path = common.check_binaries(bin)
    #         common.shell_exec('chmod +x '+bin_path,shell=True,debug=configs.debug)
    #     elif configs.update_binaries == 'yes':
    #         common.shell_exec('rm -f '+bin_path, shell=True,debug=configs.debug)
    #
    # for bin in flannel_bin_list:
    #     bin_path = common.check_binaries(bin)
    #     download_cmd = 'wget -c -P /usr/bin/ ' + \
    #                 base_url + 'flannel/' + bin
    #     if not bin_path:
    #         common.shell_exec(download_cmd,shell=True,debug=configs.debug)
    #         bin_path = common.check_binaries(bin)
    #         common.shell_exec('chmod +x '+bin_path,shell=True,debug=configs.debug)
    #     elif configs.update_binaries == 'yes':
    #         common.shell_exec('rm -f '+bin_path, shell=True,debug=configs.debug)
    #
    # for bin in util_bin_list:
    #     bin_path = common.check_binaries(bin)
    #     download_cmd = 'wget -c -P /usr/bin/ ' + \
    #                 base_url + 'util/' + bin
    #     if not bin_path:
    #         common.shell_exec(download_cmd,shell=True,debug=configs.debug)
    #         bin_path = common.check_binaries(bin)
    #         common.shell_exec('chmod +x '+bin_path,shell=True,debug=configs.debug)
    #     elif configs.update_binaries == 'yes':
    #         common.shell_exec('rm -f '+bin_path, shell=True,debug=configs.debug)



def generate_json_file(dest=None,json_obj=None):
    json_file = open(dest,'wb')
    json_file.write(json.dumps(json_obj))
    json_file.close()

#------Deployment Actions ------

def generate_cert():

    #---Get Json Schema---
    ca_csr_json = json_schema.k8s_ca_csr
    ca_config_json = json_schema.k8s_ca_config
    k8s_csr_json = json_schema.k8s_csr
    etcd_csr_json = json_schema.etcd_csr
    admin_csr_json = json_schema.k8s_admin_csr
    proxy_csr_json = json_schema.kube_proxy_csr
    flanneld_csr_json =json_schema.flanneld_csr

    #---Customize---
    k8s_cert_hosts = [
        "127.0.0.1",
        "kubernetes",
        "kubernetes.default",
        "kubernetes.default.svc",
        "kubernetes.default.svc.cluster",
        "kubernetes.default.svc.cluster.local"]

    etcd_cert_hosts = [
        "127.0.0.1"
    ]

    #-------
    haproxy_vip = configs.haproxy_vip
    haproxy_vip_arr = haproxy_vip.split(',')

    k8s_cert_hosts.append(node_ip)
    k8s_cert_hosts.append(node_name)
    k8s_cert_hosts.append(configs.cluster_kubernetes_svc_ip)
    for item in haproxy_vip_arr:
        k8s_cert_hosts.append(item)

    etcd_cert_hosts.append(node_ip)
    etcd_cert_hosts.append(node_name)

    k8s_csr_json["hosts"] = k8s_cert_hosts
    etcd_csr_json["hosts"] = etcd_cert_hosts

    # ------Prepare Directory ------
    prep_conf_dir(etcd_ssl_dir, '', clear=True)
    prep_conf_dir('/etc/kubernetes', '', clear=True)
    prep_conf_dir(k8s_ssl_dir, '', clear=True)
    prep_conf_dir('/etc/flanneld/ssl/','',clear=True)

    #---Generate Cert Files---

    generate_json_file('/etc/kubernetes/ssl/kubernetes-csr.json',k8s_csr_json)
    generate_json_file("/etc/etcd/ssl/etcd-csr.json",etcd_csr_json)
    generate_json_file(k8s_ssl_dir+'ca-config.json',ca_config_json)
    generate_json_file(k8s_ssl_dir+'ca-csr.json',ca_csr_json)
    generate_json_file(k8s_ssl_dir+'admin-csr.json',admin_csr_json)
    generate_json_file(k8s_ssl_dir+'kube-proxy-csr.json',proxy_csr_json)
    generate_json_file('/etc/flanneld/ssl/flanneld-csr.json',flanneld_csr_json)

    render(os.path.join(template_dir,"token.csv"),
           os.path.join("/etc/kubernetes/","token.csv"),
           bootstrap_token=configs.bootstrap_token)

    if not cert_tool.check_cfssl():
        print('------Installing CFSSL Tools------')
        exit(0)


    print('-----Generating CA Cert Files------')
    cert_tool.gen_ca_cert(ca_dir=k8s_ssl_dir,debug=configs.debug)
    print('-----Generating etcd Cert Files------')
    cert_tool.gen_cert_files(ca_dir=k8s_ssl_dir,profile='kubernetes',\
                             csr_file=etcd_ssl_dir+'etcd-csr.json',\
                             cert_name='etcd',\
                             dest_dir=etcd_ssl_dir,debug=configs.debug)
    print('-----Generating Flannel Cert Files------')
    cert_tool.gen_cert_files(ca_dir=k8s_ssl_dir,profile='kubernetes',\
                             csr_file='/etc/flanneld/ssl/flanneld-csr.json',\
                             cert_name='flanneld',\
                             dest_dir='/etc/flanneld/ssl/',debug=configs.debug)
    print('-----Generating k8s Admin Cert Files------')
    cert_tool.gen_cert_files(ca_dir=k8s_ssl_dir, profile='kubernetes', \
                             csr_file=k8s_ssl_dir + 'kubernetes-csr.json', \
                             cert_name='kubernetes', \
                             dest_dir=k8s_ssl_dir,debug=configs.debug)
    cert_tool.gen_cert_files(ca_dir=k8s_ssl_dir, profile='kubernetes', \
                             csr_file=k8s_ssl_dir + 'admin-csr.json', \
                             cert_name='admin', \
                             dest_dir=k8s_ssl_dir,debug=configs.debug)
    print('-----Generating kube-proxy Cert Files------')
    cert_tool.gen_cert_files(ca_dir=k8s_ssl_dir, profile='kubernetes', \
                             csr_file=k8s_ssl_dir + 'kube-proxy-csr.json', \
                             cert_name='kube-proxy', \
                             dest_dir=k8s_ssl_dir,debug=configs.debug)


def generate_kubeconfig():
    # subprocess.call([os.path.join(base_dir, "util", "generate_kubeconfig.sh"), \
    #                  kube_apiserver, bootstrap_token])

    print('------Generating kube-config------')
    shell_cmd = [os.path.join(base_dir, "util", "generate_kubeconfig.sh"), \
                     kube_apiserver, configs.bootstrap_token]
    common.shell_exec(shell_cmd,debug=configs.debug)

def get_cert_from_master():

    print('------Transporting SSL Files From Master Node------')
    prep_conf_dir('/etc/flanneld/ssl','',clear=True)
    prep_conf_dir(k8s_ssl_dir,'',clear=True)

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(configs.master_ip,22,
                configs.master_ssh_user,
                configs.master_ssh_password)
    scpclient = SCPClient(ssh.get_transport(),socket_timeout=15.0)
    scpclient.get('/etc/kubernetes/','/etc',recursive=True)
    scpclient.get('/etc/flanneld/ssl','/etc/flanneld',recursive=True)
    # sftp = paramiko.SFTPClient.from_transport(ssh.get_transport())



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
           master_ip=configs.master_ip)

    render(os.path.join(template_dir,"docker.service"),
           os.path.join(systemd_dir, "docker.service"))


def config_kubelet():
    print('------Configurating kubelet------')

    prep_conf_dir("/var/lib/kubelet",'',clear=True)
    render(os.path.join(template_dir,"kubelet.service"),
           os.path.join(systemd_dir, "kubelet.service"),
           node_ip=node_ip,
           cluster_dns_svc_ip=configs.cluster_dns_svc_ip,
           cluster_dns_domain=configs.cluster_dns_domain)

def config_apiserver():
    print('------Configurating kube-apiserver ------')

    render(os.path.join(template_dir,"kube-apiserver.service"),
           os.path.join(systemd_dir, "kube-apiserver.service"),
           master_ip=configs.master_ip,
           node_ip=node_ip,
           service_cidr=configs.service_cidr,
           node_port_range=configs.node_port_range,
           )

def config_controller_manager():
    print('------Configurating kube-controller-manager ------')

    render(os.path.join(template_dir,"kube-controller-manager.service"),
           os.path.join(systemd_dir, "kube-controller-manager.service"),
           node_ip=node_ip,
           service_cidr=configs.service_cidr,
           cluster_cidr=configs.cluster_cidr
           )

def config_scheduler():
    print('------Configurating kube-scheduler ------')
    render(os.path.join(template_dir,"kube-scheduler.service"),
           os.path.join(systemd_dir, "kube-scheduler.service"),
           node_ip=node_ip,
           service_cidr=configs.service_cidr,
           cluster_cidr=configs.cluster_cidr
           )

def config_proxy():
    print('------Configurating kube-proxy ------')

    prep_conf_dir("/var/lib/kube-proxy",'',clear=True)
    render(os.path.join(template_dir, "kube-proxy.service"),
           os.path.join(systemd_dir, "kube-proxy.service"),
           node_ip=node_ip,
           service_cidr=configs.service_cidr,
           )


def create_csr_auto_approve():
    print('------Configurating CSR Auto Approve ------')

    # rbac_cmd = "kubectl create clusterrolebinding kubelet-bootstrap --clusterrole=system:node-bootstrapper --user=kubelet-bootstrap"
    parent_folder = os.path.abspath(os.path.join(base_dir,os.path.pardir))
    addons_folder = os.path.join(parent_folder,"addons")
    csr_cmd = "kubectl create -f "+ addons_folder +"/csr-auto-approve.yml"
    # shell_exec(rbac_cmd)

    for _ in range(0,10):
        output = common.shell_exec(csr_cmd,shell=True,debug=configs.debug,output=True)
        if 'created' in output:
            break
        time.sleep(1)
        continue



    # common.shell_exec(csr_cmd,shell=True,debug=configs.debug)

def label_master_node():

    print('------Label Node as Master------')
    shell_cmd = "kubectl --kubeconfig=/etc/kubernetes/admin.kubeconfig label node "+node_ip+" node-role.kubernetes.io/master="
    common.shell_exec(shell_cmd,shell=True,debug=configs.debug)

def initiate_flanneld():
    # subprocess.call([os.path.join(base_dir, "util", "initiate_flannel.sh"), \
    #                  etcd_endpoints, flannel_etcd_prefix, cluster_cidr])
    print("------Initiating Flannel------")
    shell_cmd = [os.path.join(base_dir, "util", "initiate_flannel.sh"),etcd_endpoints, \
                 configs.flannel_etcd_prefix, configs.cluster_cidr]
    common.shell_exec(shell_cmd,shell=False,debug=configs.debug)

def start_service(service_name):
    print("------Starting Service: %s"% service_name)
    output = subprocess.check_output(["systemctl","restart",service_name])

    if 'failed' in output:
        failed_list.append(service_name)
    else:
        success_list.append(service_name)

def deploy():

    role = configs.node_role

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

    if role == 'minion':
        get_cert_from_master()
        config_flannel()
        config_proxy()
        config_kubelet()

    if role == 'master-backup':
        get_cert_from_master()
        config_flannel()
        config_apiserver()
        config_controller_manager()
        config_scheduler()
        config_proxy()
        config_kubelet()

    subprocess.call(["systemctl", "daemon-reload"])

    #------Start Service -------

    if role == 'master':

        start_service('etcd')
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

    elif role == 'minion':
        for service in node_service_list:
            start_service(service)

        print('Successfully Start Service: %s' % success_list)
        print('Failed to Start: %s' % failed_list)

    elif role == 'master-backup':

        for service in master_service_list:
            start_service(service)
        for service in node_service_list:
            start_service(service)
        print('Successfully Start Service: %s' % success_list)
        print('Failed to Start: %s' % failed_list)

        if 'kube-apiserver' in success_list \
            and 'kube-controller-manager' in success_list \
            and 'kubelet' in success_list:
            while True:
                check_node = subprocess.check_output(["kubectl","--kubeconfig=/etc/kubernetes/admin.kubeconfig","get","node"])
                if node_ip in check_node:
                    label_master_node()
                    break

def test():
    create_csr_auto_approve()

def main():
    #------ Deployment Start ------

    # --- ArgParser---
    # parser.add_argument('--conf', dest='cfgfile', default=base_dir + '/k8s.cfg', type=str,
    #                     help="the path of Kubernetes configuration file")
    # parser.add_argument('--host-ip',dest='host_ip',type=str,help="Host IP Address")
    # parser.add_argument('--role',dest='node_role',type=str,default='',required=True,help="Node Role Type:master/minion")
    parser = argparse.ArgumentParser()
    parser.add_argument('--test',dest='test_unit',type=str,default='')
    subparsers = parser.add_subparsers(help='Commands')

    parser_generate_cert = subparsers.add_parser('generate_cert', help='Generate Cert')
    parser_generate_cert.set_defaults(func=generate_cert)

    parser_deploy = subparsers.add_parser('deploy',help='Deploy Kubernetes')
    parser_deploy.set_defaults(func=deploy)

    parser_test = subparsers.add_parser('test',help='Run Tests')
    parser_test.set_defaults(func=test)

    parser_test = subparsers.add_parser('get_binaries',help='Run Tests')
    parser_test.set_defaults(func=get_binaries)

    args = parser.parse_args()
    args.func()


if __name__ == "__main__":
    main()