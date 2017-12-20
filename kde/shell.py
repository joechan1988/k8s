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


class Subcommands(object):
    def __init__(self):
        pass

    @common.arg('--config', default=constants.cluster_cfg_path, help="Default config file path")
    @common.cmd_help('Deploy a initiated kubernetes cluster according to cluster.yml')
    def deploy(self, args):
        # configs = config_parser.Config(args.config)
        # configs.load()
        # cluster_data = configs.data
        #
        # deploy.do(cluster_data)
        print("do func deploy " + args.config)

    @common.arg('--config', default=constants.cluster_cfg_path, help="Default config file path")
    def test(self, args):
        #
        # cmd = '''
        #     sysctl
        # '''
        # #
        # # cmd = 'env'
        # logging.debug(cmd)
        # ret = common.shell_exec_remote(cmd, ip='192.168.1.199', user='root', password='123456')

        print(args.config)


def get_funcs(obj):
    result = []
    for i in dir(obj):
        if callable(getattr(obj, i)) and not i.startswith('_'):
            result.append((i, getattr(obj, i)))
    return result


def main():
    # Arguments
    top_parser = argparse.ArgumentParser()
    top_parser.add_argument('--test', dest='test_unit', type=str, default='')

    # Subcommands
    subparsers = top_parser.add_subparsers(help='Commands')

    subcommands_obj = Subcommands()
    subcommands = get_funcs(subcommands_obj)

    for (func_name, func) in subcommands:

        try:
            func_help = getattr(func, 'help')
        except AttributeError as e:
            func_help = ""

        func_parser = subparsers.add_parser(func_name, help=func_help)
        func_parser.set_defaults(func=func)

        for args, kwargs in getattr(func, 'arguments', []):
            func_parser.add_argument(*args, **kwargs)

    # parser_deploy = subparsers.add_parser('deploy', help='Deploy Kubernetes')

    # parser_deploy.set_defaults(func=deploy)

    # parser_test = subparsers.add_parser('test', help='Run Tests')
    # for args, kwargs in getattr(test, 'arguments', []):
    #     parser_test.add_argument(*args, **kwargs)
    # parser_test.set_defaults(func=test)

    top_args = top_parser.parse_args()

    top_args.func(top_args)


if __name__ == "__main__":
    main()
