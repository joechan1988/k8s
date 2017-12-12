import subprocess

import os

import logging
from util import common
from templates import constants
from templates import json_schema
from util import cert_tool
from util.config_parser import Config
from service import Service

tmp_dir = constants.tmp_etcd_dir


class Etcd(Service):
    def __init__(self):
        self.cluster_type = ''
        self.service_name = 'etcd'

    def configure(self,**configs):

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

        cert_tool.generate_json_file(tmp_dir + "etcd-csr.json")

        logging.info("Generating etcd Cert Files...")
        cert_tool.gen_cert_files(ca_dir=tmp_dir, profile='kubernetes',
                                 csr_file=tmp_dir + 'etcd-csr.json',
                                 cert_name='etcd',
                                 dest_dir=tmp_dir,debug=constants.debug)

    def deploy(self):

        self._generate_cert()

        cluster_size = 0
        for node in self.nodes:
            cluster_size = cluster_size + 1

        if self.cluster_type == 'new':

            while True:
                discovery = subprocess.check_output(
                    ["curl", "-s", "https://discovery.etcd.io/new?size=" + str(cluster_size)])
                if "etcd.io" in discovery:
                    break
            # common.render(os.path.join(constants.template_dir,"etcd.service"),
            #        os.path.join(tmp_dir,"etcd.service"),
            #        node_ip=self.nodes[0].get('IP'),
            #        node_name=self.nodes[0].get('name'),
            #        discovery=discovery.replace('https','http'))

            for node in self.nodes:
                ip = node.get('external_IP')
                user = node.get('ssh_user')
                password = node.get("ssh_password")
                name = node.get("hostname")

                common.render(os.path.join(constants.template_dir, "etcd.service"),
                              os.path.join(tmp_dir, "etcd.service"),
                              node_ip=ip, node_name=name, discovery=discovery.replace('https', 'http')
                              )

                logging.info(password)

                rsh = common.RemoteShell(ip, user, password)
                rsh.connect()

                logging.info("Copy Etcd Config Files To Node: "+ name)
                rsh.copy(tmp_dir + "etcd.service", "/etc/systemd/system/")
                rsh.copy(tmp_dir + "ca.pem", self.cafile)
                rsh.copy(tmp_dir + "etcd.pem", self.certfile)
                rsh.copy(tmp_dir + "etcd-key.pem", self.keyfile)

                rsh.prep_dir("/var/lib/etcd/", clear=True)
                rsh.execute("systemctl enable etcd")

                rsh.close()


        elif self.cluster_type == "existing":
            logging.info("Using Existing etcd Cluster")

