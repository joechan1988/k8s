import os
import yaml
from yaml.parser import ParserError
import re
import logging
import common
from exception import *


class Config(object):
    def __init__(self, config_path):
        self.config_path = config_path
        self.data = None

    def _validate(self):
        """
       Constraints:
       1. control node shouldn't be either labeled as worker node
       2. required fields
       3. log level only contains following: "debug", "info", "warning", "error", "critical"

       :param cluster_data:
       :return:
       """
        config_file = file(self.config_path, 'r')
        data = yaml.load(config_file)

        ip_pattern = re.compile("^((?:(2[0-4]\d)|(25[0-5])|([01]?\d\d?))\.){3}(?:(2[0-4]\d)|(255[0-5])|([01]?\d\d?))$")

        # Top-level required fields check
        top_field_names = ['nodes', 'kubernetes', 'etcd', 'cni', 'binaries']

        for field_name in top_field_names:
            if data.get(field_name) is None:
                raise ClusterConfigError("Field {0} is missing".format(field_name))

        # Sub-level required fields check


        # Node list check:
        node_field_names = ['role', 'hostname', 'external_IP', 'ssh_user', 'ssh_password']
        for node in data.get("nodes"):
            role = node.get('role')
            name = node.get('hostname')
            ip = node.get('external_IP')
            user = node.get('ssh_user')
            password = node.get('ssh_password')

            for field_name in node_field_names:
                if node.get(field_name) is None:
                    raise ClusterConfigError("Field '{0}' in node:{1} is missing".format(field_name, name))

            if not isinstance(role, list) or len(role) == 0:
                raise ClusterConfigError("Node {0} role field is malformed".format(name))

            if not list(set(["etcd", "control", "worker"]).intersection(set(role))):
                raise ClusterConfigError(" Role:{1} of node {0} is not in 'etcd','control','worker'".format(name, role))

            if not re.match(ip_pattern, ip):
                raise ClusterConfigError("Node:{0} IP is not valid".format(name))

            if 'control' in role and 'worker' in role:
                raise ClusterConfigError(
                    "Node {0}, IP:{1} is labeled as control and worker at the same time".format(name, ip))

        # kubernetes field check
        k8s_field_names = ['version', 'service_cidr', 'cluster_cidr', 'node_port_range', 'cluster_kubernetes_svc_ip',
                           'cluster_dns_svc_ip', 'cluster_dns_domain', 'config_directory']

        for field_name in k8s_field_names:
            if data.get('kubernetes').get(field_name) is None:
                raise ClusterConfigError("Field 'kubernetes.{0}' is missing".format(field_name))

        # Log-level field check

        log_level_literal = ["debug", "info", "warning", "error", "critical"]
        log_level = data.get("log_level")
        if log_level not in log_level_literal:
            raise ClusterConfigError("Log level is set wrongly for config: {0}".format(log_level))

    @staticmethod
    def _get_etcd_endpoint(data):

        etcd_data = data.get('etcd')
        if etcd_data.get('ssl') == 'yes':
            etcd_protocol = 'https'
        else:
            etcd_protocol = 'http'

        nodes = data.get('nodes')
        etcd_eps_list = []

        for node in nodes:
            role = node.get('role')
            if 'etcd' in role:
                etcd_ep = etcd_protocol + "://" + node.get('external_IP') + ":2379"
                etcd_eps_list.append(etcd_ep)

        etcd_endpoints = ",".join(etcd_eps_list)

        return etcd_endpoints

    # @staticmethod
    # def _set_log_level(level_str):
    #     log_level = common.get_log_level(level_str)
    #     logging.basicConfig(level=log_level,
    #                     format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
    #                     datefmt='%a, %d %b %Y %H:%M:%S',
    #                     )

    def load(self):

        config_file = file(self.config_path, 'r')
        try:
            configs = yaml.load(config_file)
        except ParserError as e:
            raise ClusterConfigError("Config yaml file is malformed: {0}".format(e))

        self._validate()

        etcd_endpoints = self._get_etcd_endpoint(configs)
        configs["etcd_endpoints"] = etcd_endpoints

        self.data = configs
