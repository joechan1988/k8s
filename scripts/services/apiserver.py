import logging
from service import Service


#
# TODO: 1. Get Cert Files From etcd Node Or From /tmp/etcd/
#

class Apiserver(Service):
    def __init__(self):
        self.service_name = 'kube-apiserver'

    def configure(self, **configs):
        k8s_configs = configs.get("kubernetes")
        etcd_configs = configs.get("etcd")

        self.service_cidr = k8s_configs.get('service_cidr')
        self.node_port_range = k8s_configs.get('node_port_range')
        self.etcd_endpoints = configs.get('etcd_endpoints')
        self.etcd_cafile = etcd_configs.get('cafile')
        self.etcd_keyfile =etcd_configs.get('keyfile')
        self.etcd_certfile =etcd_configs.get('certfile')


        nodes = configs.get('nodes')

        for node in nodes:
            if 'control' in node.get('role'):
                self.nodes.append(node)


    def deploy(self):
        pass
