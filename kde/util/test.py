import common
import config_parser
from exception import *


def test_remote_shell():
    rsh = common.RemoteShell(ip="192.168.1.203", user="root", password="123456")
    if rsh.connect() != False:
        print("111")

    ret = rsh.execute("hostname")
    print(ret)


def test_config_parser():
    configs = config_parser.Config("../cluster.yml")
    try:
        configs.load()
    except BaseError as e:
        print(e.message)


def test_check_preinstalled_bins():

    ret = common.check_preinstalled_binaries("docker")
    print(ret)


def main():
    test_check_preinstalled_bins()


if __name__ == '__main__':
    main()
