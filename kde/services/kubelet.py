import logging
import os
from service import Service
from kde.util import common
from kde.templates import constants


class Kubelet(Service):
    def __init__(self):
        super(Kubelet, self).__init__()
        self.service_name = "kubelet"

    def configure(self, **cluster_data):
        k8s_data = cluster_data.get("kubernetes")

        self.cluster_dns_svc_ip = k8s_data.get("cluster_dns_svc_ip")
        self.cluster_dns_domain = k8s_data.get("cluster_dns_domain")
        self.cni_plugin = cluster_data.get("cni").get("plugin")
        #
        # nodes = cluster_data.get('nodes')
        # for node in nodes:
        #     if 'worker' in node.get('role'):
        #         self.nodes.append(node)

    def _deploy_service(self):

        # logging.info("Starting To Deploy Kubelet On Node: %s, IP address: %s ", self.host_name, self.node_ip)

        cni_enabled = False

        if self.cni_plugin in ["calico"]:
            cni_enabled = True

        if cni_enabled:
            common.render(os.path.join(constants.template_dir, "kubelet.service"),
                          os.path.join(constants.kde_service_dir, "kubelet.service"),
                          node_ip=self.node_ip,
                          cluster_dns_svc_ip=self.cluster_dns_svc_ip,
                          cluster_dns_domain=self.cluster_dns_domain,
                          cni="--network-plugin=cni")
        else:
            common.render(os.path.join(constants.template_dir, "kubelet.service"),
                          os.path.join(constants.kde_service_dir, "kubelet.service"),
                          node_ip=self.node_ip,
                          cluster_dns_svc_ip=self.cluster_dns_svc_ip,
                          cluster_dns_domain=self.cluster_dns_domain,
                          cni="")

        rsh = self.remote_shell

        rsh.prep_dir("/var/lib/kubelet/", clear=True)
        rsh.prep_dir(constants.k8s_ssl_dir)

        logging.info("Copy kubelet Config Files To Node: " + self.host_name)
        rsh.copy(constants.tmp_bin_dir + "kubelet", "/usr/bin/")
        rsh.copy(constants.kde_service_dir + "kubelet.service", "/etc/systemd/system/")
        rsh.copy(constants.kde_auth_dir + "admin.kubeconfig", "/etc/kubernetes/")

        rsh.execute("systemctl enable kubelet")
