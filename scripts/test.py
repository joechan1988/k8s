#!/usr/bin/python
# -*- coding: utf-8 -*-

from util import config_parser
from util import common
from cmd import cert, deploy
from services.etcd import Etcd
from templates import constants
import logging

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
                    datefmt='%a, %d %b %Y %H:%M:%S',
                    )


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
    cert.generate_ca_cert(constants.tmp_etcd_dir)

    etcd = Etcd()
    etcd.configure(**configs.data)

    etcd.deploy()

    ret = etcd.start()
    print(ret)


def main():
    test_config()


if __name__ == '__main__':
    main()
