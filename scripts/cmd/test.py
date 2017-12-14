import logging
import util.config_parser as config_parser
import deploy


def test_check_env():
    configs = config_parser.Config("../cluster.yml")
    configs.load()

    deploy.check_env(**configs.data)


def main():
    test_check_env()


if __name__ == '__main__':
    main()
