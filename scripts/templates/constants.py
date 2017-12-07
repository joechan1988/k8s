
import os
from util import config_parser

template_dir =  os.path.dirname(__file__)

debug = False

systemd_dir = "/etc/systemd/system/"
etcd_ssl_dir = "/etc/etcd/ssl/"
k8s_ssl_dir = "/etc/kubernetes/ssl/"