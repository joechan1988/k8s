#!/usr/bin/python
# -*- coding: utf-8 -*-

from util import config_parser
from util import common
from util.common import RemoteShell
from cmd import auth, deploy
from services.etcd import Etcd
from services.apiserver import Apiserver
from services.kubelet import Kubelet
from cmanager import CManager
from scheduler import Scheduler
from proxy import Proxy
from templates import constants
import logging

# logging.basicConfig(level=logging.INFO,
#                     format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
#                     datefmt='%a, %d %b %Y %H:%M:%S',
#                     )


def test_etcd_config():
    configs = config_parser.Config("./cluster.yml")
    configs.load()

    etcd = Etcd()

    etcd.configure(**configs.data)

    print(etcd.nodes)


def test_deploy_etcd():
    configs = config_parser.Config(constants.cluster_cfg_path)
    configs.load()

    etcd = Etcd()
    etcd.configure(**configs.data)

    etcd.deploy()

    ret = etcd.start()
    print(ret)


def test_deploy_apiserver():
    configs = config_parser.Config(constants.cluster_cfg_path)
    configs.load()

    apiserver = Apiserver()
    apiserver.configure(**configs.data)

    apiserver.deploy()

    ret = apiserver.start()
    print(ret)


def test_admin_kubeconfig():
    configs = config_parser.Config("../cluster.yml")
    configs.load()

    deploy.generate_admin_kubeconfig(**configs.data)


def test_download_bins():
    # urls = ["ftp://public:123456@joechan1988.asuscomm.com/Other/share/kubernetes/binaries/v1.8.0/server/bin/kubectl"]
    # common.download_binaries(urls)

    deploy.prep_binaries()


def test_kubelet():
    configs = config_parser.Config("../cluster.yml")
    configs.load()
    kubelet = Kubelet()
    kubelet.configure(**configs.data)

    kubelet.deploy()
    ret = kubelet.start()
    print(ret)


def test_cmanager():
    configs = config_parser.Config("../cluster.yml")
    configs.load()

    cmanager = CManager()
    cmanager.configure(**configs.data)
    cmanager.deploy()
    ret = cmanager.start()
    print(ret)


def test_scheduler():
    configs = config_parser.Config("../cluster.yml")
    configs.load()

    scheduler = Scheduler()
    scheduler.configure(**configs.data)
    scheduler.deploy()
    ret = scheduler.start()
    print(ret)


def test_proxy():
    configs = config_parser.Config("../cluster.yml")
    configs.load()

    proxy = Proxy()
    proxy.configure(**configs.data)
    proxy.deploy()
    ret = proxy.start()
    print(ret)


def stop_all(rsh=RemoteShell):
    # rsh = RemoteShell("192.168.1.203", "root", "123456")
    rsh.connect()

    rsh.execute("systemctl stop kubelet")
    rsh.execute("systemctl stop kube-apiserver")
    rsh.execute("systemctl stop etcd")
    rsh.execute("systemctl stop kube-proxy")
    rsh.execute("systemctl stop kubelet")
    rsh.execute("systemctl stop kube-scheduler")

    rsh.close()



def main():
    stop_all()
    deploy.prep_dir()
    auth.generate_ca_cert(constants.tmp_kde_dir)

    test_deploy_etcd()
    test_deploy_apiserver()
    test_admin_kubeconfig()
    test_proxy()


if __name__ == '__main__':
    main()
