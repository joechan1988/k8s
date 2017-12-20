import os
import yaml


class Config(object):
    def __init__(self, config_path):
        self.config_path = config_path
        self.data = None

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

    def load(self):
        config_file = file(self.config_path, 'r')
        configs = yaml.load(config_file)

        etcd_endpoints = self._get_etcd_endpoint(configs)
        configs["etcd_endpoints"] = etcd_endpoints

        self.data = configs
