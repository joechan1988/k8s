#!/usr/bin/python
# -*- coding: utf-8 -*-

import logging
import datetime
import shell
from cmd import auth, deploy
from kde.services import *
# from services.apiserver import Apiserver
# from services.cmanager import CManager
# from services.etcd import Etcd
# from services.kubelet import Kubelet
# from services.proxy import Proxy
# from services.scheduler import Scheduler
from kde.templates import constants
from kde.util import config_parser, common
from kde.util.common import RemoteShell
from kde.util.exception import *


# logging.basicConfig(level=logging.INFO,
#                     format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
#                     datefmt='%a, %d %b %Y %H:%M:%S',
#                     )


def test_check_env():
    configs = config_parser.Config("../cluster.yml")
    configs.load()

    try:
        deploy.pre_check(configs.data)
    except BaseError as e:
        print(e.message)


def test_validate_cluster_data():
    configs = config_parser.Config("../cluster.yml")
    configs.load()
    cluster_data = configs.data

    try:
        deploy.validate_cluster_data(cluster_data)

    except BaseException as e:
        print(e.message)


def stop_all(rsh=RemoteShell()):
    # rsh = RemoteShell("192.168.1.203", "root", "123456")

    rsh.execute("systemctl stop kubelet")
    rsh.execute("systemctl stop kube-apiserver")
    rsh.execute("systemctl stop kube-controller-manager")
    rsh.execute("systemctl stop etcd")
    rsh.execute("systemctl stop kube-proxy")
    rsh.execute("systemctl stop kubelet")
    rsh.execute("systemctl stop kube-scheduler")


def test_control_node_deploy():
    configs = config_parser.Config(constants.cluster_cfg_path)
    configs.load()

    tmp_k8s_dir = constants.tmp_kde_dir

    auth.generate_ca_cert(tmp_k8s_dir)
    auth.generate_bootstrap_token(tmp_k8s_dir)
    auth.generate_apiserver_cert(tmp_k8s_dir, configs.data)
    auth.generate_etcd_cert(tmp_k8s_dir, configs.data)
    auth.generate_admin_kubeconfig(configs.data)

    # initial deployment object
    apiserver = Apiserver()
    cmanager = CManager()
    scheduler = Scheduler()
    proxy = Proxy()
    etcd = Etcd()
    kubelet = Kubelet()

    nodes = configs.data.get("nodes")
    for node in nodes:
        ip = node.get('external_IP')
        user = node.get('ssh_user')
        password = node.get("ssh_password")
        name = node.get("hostname")

        rsh = RemoteShell(ip, user, password)
        rsh.connect()
        stop_all(rsh)

        if 'etcd' in node.get("role"):
            etcd = Etcd()
            etcd.remote_shell = rsh
            etcd.node_ip = ip
            etcd.host_name = name
            etcd.configure(**configs.data)
            etcd.deploy()

            etcd.start()

        # deploy controller component
        if 'control' in node.get('role'):

            for service in [apiserver, cmanager, scheduler, kubelet, proxy]:
                service.remote_shell = rsh
                service.node_ip = ip
                service.host_name = name
                service.configure(**configs.data)
                service.deploy()

            apiserver.start()
            scheduler.start()
            cmanager.start()
            kubelet.start()
            proxy.start()

        rsh.close()


def test_shell_getfuns():
    ret = shell._get_funcs(shell.Subcommands)
    print(ret)


def test_prep_binaries():
    configs = config_parser.Config(constants.cluster_cfg_path)
    configs.load()

    cluster_data = configs.data

    tmp_bin_path = cluster_data.get("binaries").get("path")
    try:
        deploy.prep_binaries(tmp_bin_path, cluster_data)
    except BaseError as e:
        logging.critical(e.message)


def test_recover_cert():
    cmd = """ kubectl -n kube-system get secret  calico-etcd-secrets -o json \
            |jq '.data."etcd-ca"'| sed 's/\"//g'| base64 --decode > {0} """.format("/tmp/ca.pem")
    out = common.shell_exec(cmd, shell=True, output=True)
    print(out)


def test_check_host_time():
    configs = config_parser.Config(constants.cluster_cfg_path)
    configs.load()

    cluster_data = configs.data
    # deploy.check_host_time(cluster_data)

    ret = common.shell_exec("date +'%Y-%m-%d %H:%M:%S'", shell=True, output=True)
    date_time = datetime.datetime.strptime(ret.replace("\n", ""), '%Y-%m-%d %H:%M:%S')
    print(date_time)

    # str = "2018-1-5 14:31:00"
    # str2 = "2018-1-5 14:32:00"
    # d1 = datetime.datetime.strptime(str, '%Y-%m-%d %H:%M:%S')
    # d2 = datetime.datetime.strptime(str2, '%Y-%m-%d %H:%M:%S')
    # diff = (d1-d2).seconds if d1>d2 else (d2-d1).seconds
    #
    # print (diff)


def test_get_etcd_container():
    rsh = RemoteShell("192.168.1.204", "root", "123456")
    rsh.connect()
    out = rsh.execute("docker ps -a|grep kde")

    if len(out):
        print(out)


def main():
    test_get_etcd_container()


if __name__ == '__main__':
    main()
