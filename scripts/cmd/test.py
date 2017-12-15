#!/usr/bin/python
# -*- coding: utf-8 -*-

from util import config_parser
from util import common
from util.common import RemoteShell
from cmd import auth, deploy
from services.etcd import Etcd
from services.apiserver import Apiserver
from services.kubelet import Kubelet
from services.cmanager import CManager
from services.scheduler import Scheduler
from services.proxy import Proxy
from templates import constants
import logging

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
                    datefmt='%a, %d %b %Y %H:%M:%S',
                    )


def test_check_env():
    configs = config_parser.Config("../cluster.yml")
    configs.load()

    deploy.pre_check(**configs.data)


def stop_all(rsh=RemoteShell()):
    # rsh = RemoteShell("192.168.1.203", "root", "123456")

    rsh.execute("systemctl stop kubelet")
    rsh.execute("systemctl stop kube-apiserver")
    rsh.execute("systemctl stop etcd")
    rsh.execute("systemctl stop kube-proxy")
    rsh.execute("systemctl stop kubelet")
    rsh.execute("systemctl stop kube-scheduler")


def test_control_node_deploy():
    configs = config_parser.Config(constants.cluster_cfg_path)
    configs.load()

    tmp_k8s_dir = constants.tmp_k8s_dir

    auth.generate_ca_cert(tmp_k8s_dir)
    auth.generate_bootstrap_token(tmp_k8s_dir)
    auth.generate_apiserver_cert(tmp_k8s_dir, configs.data)

    # initial deployment object
    apiserver = Apiserver()
    cmanager = CManager()

    nodes = configs.data.get("nodes")
    for node in nodes:
        ip = node.get('external_IP')
        user = node.get('ssh_user')
        password = node.get("ssh_password")
        name = node.get("hostname")

        rsh = RemoteShell(ip, user, password)
        rsh.connect()
        stop_all(rsh)

        # deploy controller component
        if 'control' in node.get('role'):
            # deploy apiserver
            apiserver.remote_shell = rsh
            apiserver.node_ip = ip
            apiserver.host_name = name
            apiserver.configure(**configs.data)
            apiserver.deploy()

            # deploy cmanager

        rsh.close()


def main():
    test_control_node_deploy()


if __name__ == '__main__':
    main()
