import subprocess

import os

from util import common
from templates import constants


class Etcd(object):

    def __init__(self):
        self.cluster_type=''


    def configure(self,**configs):

        etcd_configs = configs.get('etcd')

        self.cluster_type = etcd_configs.get('cluster_type')
        self.ssl = etcd_configs.get('ssl')
        self.keyfile = etcd_configs.get('keyfile')
        self.cafile = etcd_configs.get('cafile')
        self.certfile = etcd_configs.get('certfile')
        self.nodes = []

        nodes = configs.get('nodes')
        for node in nodes:
            if 'etcd' in node.get('role'):
                self.nodes.append(node)


    def deploy(self):

        if self.cluster_type == 'new':
            common.prep_conf_dir("/var/lib/etcd",'',clear=True)
            while True:
                discovery = subprocess.check_output(["curl", "-s", "https://discovery.etcd.io/new?size=1"])
                if "etcd.io" in discovery:
                    break

            common.render(os.path.join(constants.template_dir,"etcd.service"),
                   os.path.join(constants.systemd_dir,"etcd.service"),
                   node_ip=self.nodes[0].get('IP'),
                   node_name=self.nodes[0].get('name'),
                   discovery=discovery.replace('https','http'))

        elif self.cluster_type == "existing":
            print("Using Existing etcd Cluster")

        subprocess.call(["systemctl","enable","etcd"])

    def start(self):

        output = common.shell_exec(["systemctl","restart","etcd"],shell=False,output=True,debug=constants.debug)
        return output
