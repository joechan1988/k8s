import logging
import os
from service import Service
from kde.templates import json_schema
from kde.util import cert_tool, common
from kde.templates import constants


class Addons(Service):
    def __init__(self, addon_name):
        super(Addons, self).__init__()
        self.addon_name = addon_name

    def deploy(self):
        common.render(os.path.join(constants.template_dir, self.addon_name + ".yaml"),
                      os.path.join(constants.kde_service_dir, self.addon_name + ".yaml"),
                      )

        create_cmd = "kubectl create -f {0}".format(constants.kde_service_dir + self.addon_name + ".yaml")

        common.shell_exec(create_cmd,shell=True)
