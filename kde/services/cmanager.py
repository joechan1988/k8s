import logging
import os
from service import Service
from kde.util import common
from kde.templates import constants


class CManager(Service):
    def __init__(self):
        super(CManager, self).__init__()
        self.service_name = "kube-controller-manager"
        self.remote_shell = None
        self.node_ip = ""
        self.host_name = ""

    def configure(self, **cluster_data):
        k8s_configs = cluster_data.get("kubernetes")

        self.cni_plugin = cluster_data.get("cni").get("plugin")
        self.cluster_cidr = k8s_configs.get("cluster_cidr")
        self.service_cidr = k8s_configs.get("service_cidr")

    def _deploy_service(self):

        if self.cni_plugin == "calico":
            common.render(os.path.join(constants.template_dir, "kube-controller-manager.service"),
                          os.path.join(constants.kde_service_dir, "kube-controller-manager.service"),
                          node_ip=self.node_ip,
                          service_cidr=self.service_cidr,
                          allocate_node_cidrs="",
                          cluster_cidr=""
                          )
        else:
            common.render(os.path.join(constants.template_dir, "kube-controller-manager.service"),
                          os.path.join(constants.kde_service_dir, "kube-controller-manager.service"),
                          node_ip=self.node_ip,
                          service_cidr=self.service_cidr,
                          allocate_node_cidrs="--allocate-node-cidrs=true",
                          cluster_cidr="--cluster-cidr=" + self.cluster_cidr,
                          )

        logging.info("Copy kube-controller-manager Config Files To Node: " + self.host_name)

        rsh = self.remote_shell

        rsh.copy(constants.tmp_bin_dir + "kube-controller-manager", "/usr/bin/")
        rsh.copy(constants.kde_service_dir + "kube-controller-manager.service", "/etc/systemd/system/")

        rsh.execute("systemctl enable kube-controller-manager")
