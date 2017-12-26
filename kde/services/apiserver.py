import logging
import os
from service import Service
from kde.templates import json_schema
from kde.util import cert_tool, common
from kde.templates import constants

tmp_dir = constants.tmp_kde_dir
k8s_ssl_dir = constants.k8s_ssl_dir
tmp_bin_dir = constants.tmp_bin_dir


class Apiserver(Service):
    def __init__(self):
        super(Apiserver, self).__init__()
        self.service_name = 'kube-apiserver'
        self.node_ip = ""
        self.host_name = ""
        self.tmp_cert_path = tmp_dir
        self.remote_shell = common.RemoteShell()

    def configure(self, **configs):
        k8s_configs = configs.get("kubernetes")
        etcd_configs = configs.get("etcd")
        config_dir = k8s_configs.get("config_directory")
        ssl_dir = config_dir + "ssl/"

        self.config_dir = config_dir
        self.ssl_dir = ssl_dir
        self.service_cidr = k8s_configs.get('service_cidr')
        self.node_port_range = k8s_configs.get('node_port_range')
        self.etcd_endpoints = configs.get('etcd_endpoints')
        self.etcd_cafile = ssl_dir + "ca.pem"
        self.etcd_keyfile = ssl_dir + "etcd-key.pem"
        self.etcd_certfile = ssl_dir + "etcd.pem"
        self.etcd_ssl = etcd_configs.get('ssl')
        self.fqdn = configs.get("FQDN")

        self.ca_cert = ssl_dir + "ca.pem"
        self.ca_key = ssl_dir + "ca-key.pem"
        self.k8s_cert = ssl_dir + "kubernetes.pem"
        self.k8s_key = ssl_dir + "kubernetes-key.pem"

        #
        # nodes = configs.get('nodes')
        #
        # for node in nodes:
        #     if 'control' in node.get('role'):
        #         self.nodes.append(node)

    def _generate_cert(self):

        csr_json = json_schema.k8s_ca_csr

        cert_hosts = [
            "127.0.0.1",
            "kubernetes",
            "kubernetes.default",
            "kubernetes.default.svc",
            "kubernetes.default.svc.cluster",
            "kubernetes.default.svc.cluster.local"]

        for node in self.nodes:
            cert_hosts.append(node.get('external_IP'))
            cert_hosts.append(node.get('hostname'))
            cert_hosts.append(self.fqdn)

        csr_json["hosts"] = cert_hosts

        cert_tool.generate_json_file(tmp_dir + "kubernetes-csr.json", csr_json)

        logging.info("Generating kube-apiserver Cert Files...")
        cert_tool.gen_cert_files(ca_dir=tmp_dir, profile='kubernetes',
                                 csr_file=tmp_dir + 'kubernetes-csr.json',
                                 cert_name='kubernetes',
                                 dest_dir=tmp_dir, debug=constants.debug)

    # @staticmethod
    # def _generate_bootstrap_token():
    #
    #     cmd = "head -c 16 /dev/urandom | od -An -t x | tr -d ' '"
    #     ret = common.shell_exec(cmd, shell=True, debug=constants.debug, output=True)
    #     return ret.replace("\n", "")

    def _deploy_service(self):

        logging.info("Starting To Deploy Apiserver On Node: %s, IP address: %s ", self.host_name, self.node_ip)

        if self.etcd_ssl == 'yes':
            common.render(os.path.join(constants.template_dir, "kube-apiserver.service"),
                          os.path.join(tmp_dir, "kube-apiserver.service"),
                          node_ip=self.node_ip,
                          etcd_endpoints=self.etcd_endpoints,
                          etcd_cafile=self.etcd_cafile,
                          etcd_keyfile=self.etcd_keyfile,
                          etcd_certfile=self.etcd_certfile,
                          service_cidr=self.service_cidr,
                          node_port_range=self.node_port_range,
                          )
        else:
            common.render(os.path.join(constants.template_dir, "kube-apiserver.service"),
                          os.path.join(tmp_dir, "kube-apiserver.service"),
                          etcd_endpoints=self.etcd_endpoints,
                          etcd_cafile="",
                          etcd_keyfile="",
                          etcd_certfile="",
                          node_ip=self.node_ip,
                          service_cidr=self.service_cidr,
                          node_port_range=self.node_port_range,
                          )

        # token = self._generate_bootstrap_token()
        #
        # common.render(os.path.join(constants.template_dir, "token.csv"),
        #               os.path.join(tmp_dir, "token.csv"),
        #               bootstrap_token=token)

        logging.info("Copy kube-apiserver Config Files To Node: " + self.host_name)
        rsh = self.remote_shell
        rsh.prep_dir(self.ssl_dir, clear=True)

        rsh.copy(tmp_bin_dir + "kube-apiserver", "/usr/bin/")
        rsh.copy(tmp_dir + "kube-apiserver.service", "/etc/systemd/system/")
        rsh.copy(self.tmp_cert_path + "token.csv", self.config_dir)
        rsh.copy(self.tmp_cert_path + "ca.pem", self.ca_cert)
        rsh.copy(self.tmp_cert_path + "ca-key.pem", self.ca_key)
        rsh.copy(self.tmp_cert_path + "kubernetes.pem", self.k8s_cert)
        rsh.copy(self.tmp_cert_path + "kubernetes-key.pem", self.k8s_key)
        rsh.copy(self.tmp_cert_path + "etcd.pem", self.etcd_certfile)
        rsh.copy(self.tmp_cert_path + "etcd-key.pem", self.etcd_keyfile)

        rsh.execute("systemctl enable kube-apiserver")
