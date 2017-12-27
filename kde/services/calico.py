import logging
import os
from service import Service
from kde.templates import json_schema
from kde.util import cert_tool, common
from kde.templates import constants

etcd_ssl_dir = constants.etcd_ssl_dir

class Calico(Service):
    def __init__(self):
        super(Calico, self).__init__()
        self.service_name = "Calico"
        self.remote_shell = None

    def configure(self, **cluster_data):
        k8s_configs = cluster_data.get("kubernetes")
        etcd_configs = cluster_data.get('etcd')

        self.cluster_cidr = k8s_configs.get("cluster_cidr")
        self.etcd_endpoints = cluster_data.get("etcd_endpoints")
        self.etcd_keyfile = etcd_configs.get('keyfile')
        self.etcd_cafile = etcd_configs.get('cafile')
        self.etcd_certfile = etcd_configs.get('certfile')

    def _deploy_service(self):
        common.render(os.path.join(constants.template_dir, "calico.yaml"),
                      os.path.join(constants.kde_service_dir, "calico.yaml"),
                      etcd_endpoints=self.etcd_endpoints,
                      etcd_keyfile=self.etcd_keyfile,
                      etcd_cafile=self.etcd_cafile,
                      etcd_certfile=self.etcd_certfile,
                      cluster_cidr=self.cluster_cidr
                      )

        rsh = self.remote_shell
        rsh.prep_dir(constants.kde_service_dir, clear=False)
        rsh.copy(constants.kde_service_dir + "calico.yaml", constants.kde_service_dir + "calico.yaml")


        # Get calicoctl

    def start(self):
        logging.critical("Creating Calico CNI plugin in cluster")

        rsh = self.remote_shell

        # Create calico cluster secret
        create_secret_cmd = "kubectl -n kube-system create secret generic calico-etcd-secrets \
                                --from-file=etcd-ca=" + etcd_ssl_dir + "ca.pem \
                                --from-file=etcd-cert=" + etcd_ssl_dir + "etcd.pem \
                                --from-file=etcd-key=" + etcd_ssl_dir + "etcd-key.pem"

        # Create calico k8s application
        create_calico_cmd = "kubectl -n kube-system create -f " + constants.kde_service_dir + "calico.yaml"

        outputs = rsh.execute(create_secret_cmd)
        logging.debug(outputs)
        for output in outputs:
            if "Error from server" in output or "error" in output:
                logging.error("Failed to create calico cluster secret: {0}".format(output))
                return False

        logging.debug("Created calico cluster secret")

        outputs = rsh.execute(create_calico_cmd)
        logging.debug(outputs)
        for output in outputs:
            if "Error from server" in output:
                logging.error("Failed to create calico cni plugin: {0}".format(output))
                return False

        # Configure calico outgoing traffic policy

        logging.critical("Finished creating calico cni plugin")
        return True
