import subprocess

import os

import logging
from kde.util import common
from kde.templates import constants,json_schema
from kde.util import cert_tool
from service import Service

tmp_dir = constants.tmp_etcd_dir
tmp_bin_dir = constants.tmp_bin_dir
tmp_k8s_dir = constants.tmp_k8s_dir


class Etcd(Service):
    def __init__(self):
        super(Etcd, self).__init__()
        self.cluster_type = ''
        self.service_name = 'etcd'
        self.nodes = []
        self.tmp_cert_path = tmp_dir

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

        cert_tool.generate_json_file(tmp_dir + "etcd-csr.json", csr_json)

        logging.info("Generating etcd Cert Files...")
        cert_tool.gen_cert_files(ca_dir=tmp_k8s_dir, profile='kubernetes',
                                 csr_file=tmp_dir + 'etcd-csr.json',
                                 cert_name='etcd',
                                 dest_dir=tmp_dir, debug=constants.debug)

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
                          os.path.join(tmp_dir, "etcd.service"),
                          node_ip=self.node_ip, node_name=self.host_name, discovery=discovery.replace('https', 'http')
                          )

            # logging.info(password)

            rsh = self.remote_shell
            # rsh.connect()

            logging.info("Copy Etcd Config Files To Node: " + self.host_name)
            rsh.prep_dir("/etc/etcd/ssl/", clear=True)
            rsh.copy(tmp_bin_dir + "etcd", "/usr/bin/")
            rsh.copy(tmp_dir + "etcd.service", "/etc/systemd/system/")
            rsh.copy(self.tmp_cert_path + "ca.pem", self.cafile)
            rsh.copy(self.tmp_cert_path + "etcd.pem", self.certfile)
            rsh.copy(self.tmp_cert_path + "etcd-key.pem", self.keyfile)

            rsh.prep_dir("/var/lib/etcd/", clear=True)
            rsh.execute("systemctl enable etcd")

            # rsh.close()

        elif self.cluster_type == "existing":
            logging.info("Using Existing etcd Cluster")
