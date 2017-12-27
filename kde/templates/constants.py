import os

cluster_cfg_path = "/root/codes/k8s-deploy/kde/cluster.yml"

template_dir = os.path.dirname(__file__)

default_log_level = "INFO"

# System-preset directories
systemd_dir = "/etc/systemd/system/"



etcd_ssl_dir = "/etc/etcd/ssl/"
k8s_ssl_dir = "/etc/kubernetes/ssl/"

# Manifest directories

kde_dir = "/etc/kde/"
kde_auth_dir = "/etc/kde/auth/"
kde_service_dir = "/etc/kde/service/"

# Settings for local execution
debug = True

# Deprecated temp dirs

tmp_dir = "/tmp/"
tmp_kde_dir = "/tmp/kde/"
tmp_etcd_dir = "/tmp/etcd/"
tmp_bin_dir = "/tmp/bin/"