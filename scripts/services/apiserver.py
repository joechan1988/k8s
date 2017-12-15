import logging
import os
from service import Service
from templates import json_schema
from util import cert_tool, common
from templates import constants

tmp_dir = constants.tmp_k8s_dir
k8s_ssl_dir = constants.k8s_ssl_dir
tmp_bin_dir = constants.tmp_bin_dir


#
# TODO: 1. Get Cert Files From etcd Node Or From /tmp/etcd/
# TODO: 2. k8s cert file: self.cafile,self.keyfile, ... ; rsh copy cert file
#


class Apiserver(Service):
    def __init__(self):
        super(Apiserver, self).__init__()
        self.service_name = 'kube-apiserver'
        self.node_ip = ""
        self.host_name = ""
        self.remote_shell = common.RemoteShell()

    def configure(self, **configs):
        k8s_configs = configs.get("kubernetes")
        etcd_configs = configs.get("etcd")

        self.service_cidr = k8s_configs.get('service_cidr')
        self.node_port_range = k8s_configs.get('node_port_range')
        self.etcd_endpoints = configs.get('etcd_endpoints')
        self.etcd_cafile = etcd_configs.get('cafile')
        self.etcd_keyfile = etcd_configs.get('keyfile')
        self.etcd_certfile = etcd_configs.get('certfile')
        self.etcd_ssl = etcd_configs.get('ssl')
        self.fqdn = configs.get("FQDN")

        self.ca_cert = k8s_ssl_dir + "ca.pem"
        self.ca_key = k8s_ssl_dir + "ca-key.pem"
        self.k8s_cert = k8s_ssl_dir + "kubernetes.pem"
        self.k8s_key = k8s_ssl_dir + "kubernetes-key.pem"

        nodes = configs.get('nodes')

        for node in nodes:
            if 'control' in node.get('role'):
                self.nodes.append(node)

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

    @staticmethod
    def _generate_bootstrap_token():

        cmd = "head -c 16 /dev/urandom | od -An -t x | tr -d ' '"
        ret = common.shell_exec(cmd, shell=True, debug=constants.debug, output=True)
        return ret.replace("\n", "")

    def deploy(self):

        # self._generate_cert()

        # for node in self.nodes:
        #     ip = node.get('external_IP')
        #     user = node.get('ssh_user')
        #     password = node.get("ssh_password")
        #     name = node.get("hostname")

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
        # rsh = common.RemoteShell(ip, user, password)
        rsh = self.remote_shell
        rsh.prep_dir(k8s_ssl_dir, clear=True)

        rsh.copy(tmp_bin_dir + "kube-apiserver", "/usr/bin/")
        rsh.copy(tmp_dir + "kube-apiserver.service", "/etc/systemd/system/")
        rsh.copy(tmp_dir + "token.csv", "/etc/kubernetes/")
        rsh.copy(tmp_dir + "ca.pem", self.ca_cert)
        rsh.copy(tmp_dir + "ca-key.pem", self.ca_key)
        rsh.copy(tmp_dir + "kubernetes.pem", self.k8s_cert)
        rsh.copy(tmp_dir + "kubernetes-key.pem", self.k8s_key)

        rsh.execute("systemctl enable kube-apiserver")

            # rsh.close()
