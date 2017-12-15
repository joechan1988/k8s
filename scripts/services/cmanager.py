import logging
import os
from service import Service
from templates import json_schema
from util import cert_tool, common
from templates import constants

tmp_dir = constants.tmp_k8s_dir
k8s_ssl_dir = constants.k8s_ssl_dir
tmp_bin_dir = constants.tmp_bin_dir


class CManager(Service):
    def __init__(self):
        super(CManager, self).__init__()
        self.service_name = "kube-controller-manager"

    def configure(self, **cluster_data):
        k8s_configs = cluster_data.get("kubernetes")

        self.cluster_cidr = k8s_configs.get("cluster_cidr")
        self.service_cidr = k8s_configs.get("service_cidr")

        nodes = cluster_data.get('nodes')

        for node in nodes:
            if 'control' in node.get('role'):
                self.nodes.append(node)

    def deploy(self):

        for node in self.nodes:
            ip = node.get('external_IP')
            user = node.get('ssh_user')
            password = node.get("ssh_password")
            name = node.get("hostname")

            logging.info("Starting To Deploy Controller Manager On Node: %s, IP address: %s ", name, ip)

            common.render(os.path.join(constants.template_dir, "kube-controller-manager.service"),
                          os.path.join(tmp_dir, "kube-controller-manager.service"),
                          node_ip=ip,
                          service_cidr=self.service_cidr,
                          cluster_cidr=self.cluster_cidr,
                          )

            logging.info("Copy kube-controller-manager Config Files To Node: " + name)

            rsh = common.RemoteShell(ip, user, password)
            rsh.connect()

            rsh.copy(tmp_bin_dir+"kube-controller-manager","/usr/bin/")
            rsh.copy(tmp_dir + "kube-controller-manager.service", "/etc/systemd/system/")

            rsh.execute("systemctl enable kube-controller-manager")

            rsh.close()


