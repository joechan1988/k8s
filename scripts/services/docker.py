import logging
import os
from service import Service
from templates import json_schema
from util import cert_tool, common
from templates import constants

tmp_dir = constants.tmp_k8s_dir
k8s_ssl_dir = constants.k8s_ssl_dir


class Docker(Service):
    def __init__(self):
        super(Docker, self).__init__()
        self.service_name = "docker"

    def configure(self):
        pass

    def deploy(self):
        common.render(os.path.join(constants.template_dir, "docker.service"),
                      os.path.join(tmp_dir, "docker.service"))
