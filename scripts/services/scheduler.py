import logging
import os
from service import Service
from templates import json_schema
from util import cert_tool, common
from templates import constants

tmp_dir = constants.tmp_k8s_dir
k8s_ssl_dir = constants.k8s_ssl_dir
tmp_bin_dir = constants.tmp_bin_dir


class Scheduler(Service):
    def __init__(self):
        super(Scheduler, self).__init__()
        self.service_name = "kube-scheduler"

    def configure(self, **cluster_data):
        #
        # nodes = cluster_data.get('nodes')
        #
        # for node in nodes:
        #     if 'control' in node.get('role'):
        #         self.nodes.append(node)
        pass

    def _deploy_service(self):
        #
        # for node in self.nodes:
        #     ip = node.get('external_IP')
        #     user = node.get('ssh_user')
        #     password = node.get("ssh_password")
        #     name = node.get("hostname")

        logging.info("Starting To Deploy Scheduler On Node: %s, IP address: %s ", self.host_name, self.node_ip)

        common.render(os.path.join(constants.template_dir, "kube-scheduler.service"),
                      os.path.join(tmp_dir, "kube-scheduler.service"),
                      node_ip=self.node_ip,
                      )

        logging.info("Copy kube-scheduler Config Files To Node: " + self.host_name)

        rsh = self.remote_shell
        # rsh.connect()

        rsh.copy(tmp_bin_dir + "kube-scheduler", "/usr/bin/")
        rsh.copy(tmp_dir + "kube-scheduler.service", "/etc/systemd/system/")

        rsh.execute("systemctl enable kube-scheduler")

        # rsh.close()
