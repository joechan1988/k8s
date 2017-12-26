#!/usr/bin/python
# -*- coding: utf-8 -*-

from util import config_parser
from util import common
from cmd import auth, deploy
from services.etcd import Etcd
from services.apiserver import Apiserver
from services.kubelet import Kubelet
from templates import constants
import shell
import random, string
import logging


#
# logging.basicConfig(level=logging.INFO,
#                     format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
#                     datefmt='%a, %d %b %Y %H:%M:%S',
#                     )



def test_config():
    configs = config_parser.Config("./cluster.yml")
    configs.load()

    print(configs.data.get('etcd_endpoints'))


def test_etcd_config():
    configs = config_parser.Config("./cluster.yml")
    configs.load()

    etcd = Etcd()

    etcd.configure(**configs.data)

    print(etcd.nodes)


def test_rsh():
    rsh = common.RemoteShell(ip="192.168.1.201", user="root", password="123456")
    rsh.connect()

    rsh.prep_dir("/tmp/123", clear=False)

    rsh.copy("/etc/yum.repos.d/", "/tmp/123/")

    rsh.close()

    # common.prep_dir_remote("/tmp/123/","",ip="192.168.1.201",user="root",password="123456",clear=True)


def test_deploy_etcd():
    configs = config_parser.Config("./cluster.yml")
    configs.load()

    deploy.prep_dir()
    auth.generate_ca_cert(constants.tmp_etcd_dir)

    etcd = Etcd()
    etcd.configure(**configs.data)

    etcd.deploy()

    ret = etcd.start()
    print(ret)


def test_deploy_apiserver():
    configs = config_parser.Config("./cluster.yml")
    configs.load()

    deploy.prep_dir()
    auth.generate_ca_cert(constants.tmp_kde_dir)

    apiserver = Apiserver()
    apiserver.configure(**configs.data)

    apiserver.deploy()

    ret = apiserver.start()
    print(ret)


def test_admin_kubeconfig():
    deploy.generate_admin_kubeconfig()


def test_download_bins():
    # urls = ["ftp://public:123456@joechan1988.asuscomm.com/Other/share/kubernetes/binaries/v1.8.0/server/bin/kubectl"]
    # common.download_binaries(urls)

    deploy.prep_binaries()


def test_kubelet():
    configs = config_parser.Config("./cluster.yml")
    configs.load()
    kubelet = Kubelet()
    kubelet.configure(**configs.data)

    kubelet.deploy()
    ret = kubelet.start()
    print(ret)


def test_shell():
    """
    Test Case:
        1. Exception:
            a. cluster.yml validation
            b. failed service
            c. failed node

    :return:
    """
    shell.main()


def test_bak_etcd():
    bak_dir_name = "etcd_bak_"+"".join(random.sample(string.ascii_letters + string.digits, 8))
    print(bak_dir_name)


def main():
    test_bak_etcd()


if __name__ == '__main__':
    main()
