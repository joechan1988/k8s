import logging
from templates import json_schema, constants
from util import cert_tool


def generate_ca_cert(path):
    ca_csr_json = json_schema.k8s_ca_csr
    ca_config_json = json_schema.k8s_ca_config

    cert_tool.generate_json_file(path + 'ca-config.json', ca_config_json)
    cert_tool.generate_json_file(path + 'ca-csr.json', ca_csr_json)

    logging.info("---Generating CA Cert Files---")
    cert_tool.gen_ca_cert(ca_dir=path, debug=constants.debug)


def generate_kubeconfig():
    pass
