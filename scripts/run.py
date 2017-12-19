#!/usr/bin/python
# -*- coding: utf-8 -*-
import os
import logging
import argparse
from util import common, config_parser
from cmd import deploy
from templates import constants

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
                    datefmt='%a, %d %b %Y %H:%M:%S',
                    )


# ------Global Vars-----

# Subcommands

@common.arg('config', default='')
def deploy():
    pass


@common.arg('--config', default=constants.cluster_cfg_path, help="Default config file path")
def test(args):
    #
    # cmd = '''
    #     sysctl
    # '''
    # #
    # # cmd = 'env'
    # logging.debug(cmd)
    # ret = common.shell_exec_remote(cmd, ip='192.168.1.199', user='root', password='123456')

    print(args.config)


def main():
    # Arguments
    top_parser = argparse.ArgumentParser()
    top_parser.add_argument('--test', dest='test_unit', type=str, default='')
    # parser.add_argument("--config",type=str,default=constants.cluster_cfg_path)

    # Subcommands
    subparsers = top_parser.add_subparsers(help='Commands')
    parser_generate_cert = subparsers.add_parser('generate_cert', help='Generate Cert')
    # parser_generate_cert.set_defaults(func=generate_cert)

    parser_deploy = subparsers.add_parser('deploy', help='Deploy Kubernetes')

    # parser_deploy.set_defaults(func=deploy)

    parser_test = subparsers.add_parser('test', help='Run Tests')
    for args, kwargs in getattr(test, 'arguments', []):
        parser_test.add_argument(*args, **kwargs)
    parser_test.set_defaults(func=test)

    parser_test = subparsers.add_parser('get_binaries', help='Run Tests')
    # parser_test.set_defaults(func=get_binaries)

    top_args = top_parser.parse_args()

    top_args.func(args)


if __name__ == "__main__":
    main()
