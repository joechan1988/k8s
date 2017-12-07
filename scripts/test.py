#!/usr/bin/python
# -*- coding: utf-8 -*-

from services.etcd import Etcd
from util import config_parser


def test_etcd():

    configs = config_parser.Config("./cluster.yml")
    configs.load()

    etcd = Etcd()

    etcd.configure(**configs.data)

    print(etcd.nodes)



def main():

    test_etcd()



if __name__ == '__main__':
    main()