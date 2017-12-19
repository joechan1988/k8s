import logging
import os
from service import Service
from templates import json_schema
from util import cert_tool, common
from templates import constants

tmp_dir = constants.tmp_k8s_dir
k8s_ssl_dir = constants.k8s_ssl_dir
tmp_bin_dir = constants.tmp_bin_dir


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

        logging.info("Starting To Deploy Kubelet On Node: %s, IP address: %s ", self.host_name, self.node_ip)

        cni_enabled = False

        if self.cni_plugin in ["calico"]:
            cni_enabled = True

        # for node in self.nodes:
        #     ip = node.get('external_IP')
        #     user = node.get('ssh_user')
        #     password = node.get("ssh_password")
        #     name = node.get("hostname")

        if cni_enabled:
            common.render(os.path.join(constants.template_dir, "kubelet.service"),
                          os.path.join(tmp_dir, "kubelet.service"),
                          node_ip=self.node_ip,
                          cluster_dns_svc_ip=self.cluster_dns_svc_ip,
                          cluster_dns_domain=self.cluster_dns_domain,
                          cni="--network-plugin=cni")
        else:
            common.render(os.path.join(constants.template_dir, "kubelet.service"),
                          os.path.join(tmp_dir, "kubelet.service"),
                          node_ip=self.node_ip,
                          cluster_dns_svc_ip=self.cluster_dns_svc_ip,
                          cluster_dns_domain=self.cluster_dns_domain,
                          cni="")

        rsh = self.remote_shell
        # rsh.connect()

        logging.info("Copy kubelet Config Files To Node: " + self.host_name)
        rsh.copy(tmp_bin_dir+"kubelet","/usr/bin/")
        rsh.copy(tmp_dir + "kubelet.service", "/etc/systemd/system/")
        rsh.copy(tmp_dir + "admin.kubeconfig", "/etc/kubernetes/")

        rsh.prep_dir("/var/lib/kubelet/", clear=True)
        rsh.execute("systemctl enable kubelet")

        # rsh.close()
