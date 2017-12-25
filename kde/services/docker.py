import logging
import os
from service import Service
from kde.util import common
from kde.templates import constants

tmp_dir = constants.tmp_kde_dir
k8s_ssl_dir = constants.k8s_ssl_dir


class Docker(Service):
    def __init__(self):
        super(Docker, self).__init__()
        self.service_name = "docker"

    def configure(self,**cluster_data):
        self.cni_plugin = cluster_data.get("cni").get("plugin")

    def _deploy_service(self):

        if self.cni_plugin == "flannel":
            flannel_env_file = "EnvironmentFile=-/run/flannel/docker"
            common.render(os.path.join(constants.template_dir, "docker.service"),
                          os.path.join(tmp_dir, "docker.service"),
                          flannel_env_file=flannel_env_file)

        else:
            common.render(os.path.join(constants.template_dir, "docker.service"),
                          os.path.join(tmp_dir, "docker.service"),
                          flannel_env_file="")

        rsh = self.remote_shell
        rsh.copy(tmp_dir + "docker.service", "/etc/systemd/system/")
        rsh.execute("systemctl enable docker")