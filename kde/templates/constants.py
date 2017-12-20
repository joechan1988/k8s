import os
from kde.util import config_parser

template_dir = os.path.dirname(__file__)

debug = True

tmp_dir = "/tmp/"
tmp_k8s_dir = "/tmp/k8s/"
tmp_etcd_dir = "/tmp/etcd/"
tmp_bin_dir = "/tmp/bin/"
systemd_dir = "/etc/systemd/system/"
etcd_ssl_dir = "/etc/etcd/ssl/"
k8s_ssl_dir = "/etc/kubernetes/ssl/"

cluster_cfg_path = "/root/codes/k8s-deploy/scripts/cluster.yml"