import logging
import os
from templates import json_schema, constants
from util import cert_tool, common, config_parser

tmp_k8s_dir = constants.tmp_k8s_dir


def generate_ca_cert(path):
    ca_csr_json = json_schema.k8s_ca_csr
    ca_config_json = json_schema.k8s_ca_config

    cert_tool.generate_json_file(path + 'ca-config.json', ca_config_json)
    cert_tool.generate_json_file(path + 'ca-csr.json', ca_csr_json)

    logging.info("---Generating CA Cert Files---")
    cert_tool.gen_ca_cert(ca_dir=path, debug=constants.debug)


def generate_bootstrap_token(path):
    cmd = "head -c 16 /dev/urandom | od -An -t x | tr -d ' '"
    ret = common.shell_exec(cmd, shell=True, debug=constants.debug, output=True)
    bootstrap_token = ret.replace("\n", "")

    common.render(os.path.join(constants.template_dir, "token.csv"),
                  os.path.join(path, "token.csv"),
                  bootstrap_token=bootstrap_token)


def generate_apiserver_cert(path, cluster_data):
    csr_json = json_schema.k8s_ca_csr

    nodes = cluster_data.get("nodes")

    cert_hosts = [
        "127.0.0.1",
        "kubernetes",
        "kubernetes.default",
        "kubernetes.default.svc",
        "kubernetes.default.svc.cluster",
        "kubernetes.default.svc.cluster.local"]

    for node in nodes:
        if node.get("role") == "control":
            cert_hosts.append(node.get("external_IP"))
            cert_hosts.append(node.get("hostname"))

    csr_json["hosts"] = cert_hosts
    cert_tool.generate_json_file(tmp_k8s_dir + "kubernetes-csr.json", csr_json)

    logging.info("Generating kube-apiserver Cert Files...")
    cert_tool.gen_cert_files(ca_dir=path, profile='kubernetes',
                             csr_file=path + 'kubernetes-csr.json',
                             cert_name='kubernetes',
                             dest_dir=path, debug=constants.debug)


def generate_kubeconfig():
    pass
