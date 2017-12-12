import os
from util import common
from templates import constants


def prep_dir():
    common.prep_conf_dir(constants.tmp_etcd_dir, '', clear=True)
    common.prep_conf_dir(constants.tmp_k8s_dir, '', clear=True)


def deploy():
    print("---Generating CA Cert---")
