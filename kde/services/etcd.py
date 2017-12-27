import subprocess

import os

import logging
from kde.util import common
from kde.templates import constants, json_schema
from kde.util import cert_tool
from service import Service


class Etcd(Service):
    def __init__(self):
        super(Etcd, self).__init__()
        self.cluster_type = ''
        self.service_name = 'etcd'
        self.nodes = []

    def configure(self, **configs):

        etcd_configs = configs.get('etcd')

        self.cluster_type = etcd_configs.get('cluster_type')
        self.ssl = etcd_configs.get('ssl')
        self.keyfile = etcd_configs.get('keyfile')
        self.cafile = etcd_configs.get('cafile')
        self.certfile = etcd_configs.get('certfile')

        nodes = configs.get('nodes')
        for node in nodes:
            if 'etcd' in node.get('role'):
                self.nodes.append(node)

    def _generate_cert(self):

        csr_json = json_schema.etcd_csr

        cert_hosts = [
            "127.0.0.1"
        ]

        for node in self.nodes:
            cert_hosts.append(node.get('external_IP'))
            cert_hosts.append(node.get('hostname'))

        csr_json["hosts"] = cert_hosts

        cert_tool.generate_json_file(constants.kde_auth_dir + "etcd-csr.json", csr_json)

        logging.info("Generating etcd Cert Files...")
        cert_tool.gen_cert_files(ca_dir=constants.kde_auth_dir, profile='kubernetes',
                                 csr_file=constants.kde_auth_dir + 'etcd-csr.json',
                                 cert_name='etcd',
                                 dest_dir=constants.kde_auth_dir, debug=constants.debug)

    def _deploy_service(self):

        # self._generate_cert()

        cluster_size = 0
        for node in self.nodes:
            cluster_size = cluster_size + 1

        if self.cluster_type == 'new':

            while True:
                discovery = subprocess.check_output(
                    ["curl", "-s", "https://discovery.etcd.io/new?size=" + str(cluster_size)])
                if "etcd.io" in discovery:
                    break

            # for node in self.nodes:
            #     ip = node.get('external_IP')
            #     user = node.get('ssh_user')
            #     password = node.get("ssh_password")
            #     name = node.get("hostname")

            common.render(os.path.join(constants.template_dir, "etcd.service"),
                          os.path.join(constants.kde_service_dir, "etcd.service"),
                          node_ip=self.node_ip, node_name=self.host_name, discovery=discovery.replace('https', 'http')
                          )

            # logging.info(password)

            rsh = self.remote_shell
            # rsh.connect()

            logging.info("Copy Etcd Config Files To Node: " + self.host_name)
            rsh.prep_dir("/etc/etcd/ssl/", clear=True)
            rsh.copy(constants.tmp_bin_dir + "etcd", "/usr/bin/")
            rsh.copy(constants.kde_service_dir + "etcd.service", "/etc/systemd/system/")
            rsh.copy(constants.kde_auth_dir + "ca.pem", self.cafile)
            rsh.copy(constants.kde_auth_dir + "etcd.pem", self.certfile)
            rsh.copy(constants.kde_auth_dir + "etcd-key.pem", self.keyfile)

            rsh.prep_dir("/var/lib/etcd/", clear=True)
            rsh.execute("systemctl enable etcd")

            # rsh.close()

        elif self.cluster_type == "existing":
            logging.critical("Using Existing etcd Cluster")
