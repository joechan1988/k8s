import os
from kde.util import config_parser

cluster_cfg_path = "/root/codes/k8s-deploy/kde/cluster.yml"

template_dir = os.path.dirname(__file__)

default_log_level = "INFO"

tmp_dir = "/tmp/"
tmp_kde_dir = "/tmp/kde/"
tmp_etcd_dir = "/tmp/etcd/"
tmp_bin_dir = "/tmp/bin/"
systemd_dir = "/etc/systemd/system/"
etcd_ssl_dir = "/etc/etcd/ssl/"
k8s_ssl_dir = "/etc/kubernetes/ssl/"

# Settings for local execution
debug = True
