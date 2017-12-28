import subprocess

import os

import logging
from kde.util import common
from kde.templates import constants
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

        cluster_size = 0
        for node in self.nodes:
            cluster_size = cluster_size + 1

        while True:
            discovery = subprocess.check_output(
                ["curl", "-s", "https://discovery.etcd.io/new?size=" + str(cluster_size)])
            if "etcd.io" in discovery:
                break

        self.discovery = discovery.replace('https', 'http')

    def _deploy_service(self):

        if self.cluster_type == 'new':

            # common.render(os.path.join(constants.template_dir, "etcd.service"),
            #               os.path.join(constants.kde_service_dir, "etcd.service"),
            #               node_ip=self.node_ip, node_name=self.host_name,
            #               discovery=self.discovery.replace('https', 'http')
            #               )

            rsh = self.remote_shell

            logging.info("Copy Etcd Config Files To Node: " + self.host_name)
            rsh.prep_dir("/etc/etcd/ssl/", clear=True)
            rsh.copy(constants.tmp_bin_dir + "etcd", "/usr/bin/")
            # rsh.copy(constants.kde_service_dir + "etcd.service", "/etc/systemd/system/")
            rsh.copy(constants.kde_auth_dir + "ca.pem", self.cafile)
            rsh.copy(constants.kde_auth_dir + "etcd.pem", self.certfile)
            rsh.copy(constants.kde_auth_dir + "etcd-key.pem", self.keyfile)

            rsh.prep_dir("/var/lib/etcd/", clear=True)
            # rsh.execute("systemctl enable etcd")

        elif self.cluster_type == "existing":
            logging.critical("Using Existing etcd Cluster")

    def start(self):
        logging.critical("Starting " + self.service_name + " Service On Node: " + self.host_name)
        rsh = self.remote_shell
        # rsh.connect()

        cmd = "docker run -d --name kde-etcd \
                -v {keyfile}:{keyfile} \
                -v {cafile}:{cafile} \
                -v {certfile}:{certfile} \
                -v /var/lib/etcd:/var/lib/etcd \
              --net=host --privileged --restart=on-failure \
                gcr.io/google-containers/etcd:3.1.11 etcd \
              --name={name} \
              --cert-file={certfile} \
              --key-file={keyfile} \
              --peer-cert-file={certfile} \
              --peer-key-file={keyfile} \
              --trusted-ca-file={cafile} \
              --peer-trusted-ca-file={cafile} \
              --initial-advertise-peer-urls=https://{node_ip}:2380 \
              --listen-peer-urls=https://{node_ip}:2380 \
              --listen-client-urls=https://{node_ip}:2379,http://127.0.0.1:2379 \
              --advertise-client-urls=https://{node_ip}:2379 \
              --discovery={discovery} \
              --data-dir=/var/lib/etcd".format(discovery=self.discovery,
                                               keyfile=self.keyfile,
                                               cafile=self.cafile,
                                               certfile=self.certfile,
                                               node_ip=self.node_ip,name=self.host_name)

        logging.info(cmd)
        # rsh.execute("systemctl daemon-reload")
        container_id = rsh.execute(cmd)
        logging.info(container_id)
        output = "docker ps -a|grep {0}".format(container_id)

        if output and "Exited" in output[0]:
            logging.error(output)
            logging.error("Failed To Start Service: " + self.service_name + " On Node: " + self.host_name)
            return False
        else:
            logging.critical("Finished Starting Service: " + self.service_name + " On Node: " + self.host_name)
            return True
