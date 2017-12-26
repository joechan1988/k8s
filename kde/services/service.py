import logging
from kde.util.common import RemoteShell


class Service(object):
    def __init__(self):
        self.service_name = ''
        self.node_ip = ''
        self.host_name = ''
        self.remote_shell = RemoteShell()

    def deploy(self):

        logging.info("Deploying Service: " + self.service_name + " On Node: " + self.host_name)

        self._deploy_service()

        logging.info("Finished Deploying Service: " + self.service_name + " On Node: " + self.host_name)

    def _deploy_service(self):
        pass

    def configure(self):
        pass

    def start(self):

        logging.info("Starting " + self.service_name + " Service On Node: " + self.host_name)
        rsh = self.remote_shell
        # rsh.connect()

        rsh.execute("systemctl daemon-reload")
        output = rsh.execute("systemctl restart " + self.service_name)
        # logging.info(output)

        if output and "failed" in output[0]:
            logging.error(output)
            logging.error("Failed To Start Service: " + self.service_name + " On Node: " + self.host_name)
            return False
        else:
            logging.critical("Finished Starting Service: " + self.service_name + " On Node: " + self.host_name)
            return True

    def stop(self):
        logging.info("Stopping " + self.service_name + " Service On Node: " + self.host_name)
        rsh = self.remote_shell

        rsh.execute("systemctl stop " + self.service_name)
