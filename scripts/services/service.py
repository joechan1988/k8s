import logging
from util.common import RemoteShell


class Service(object):
    def __init__(self):
        self.service_name = ''
        self.nodes=[]

    def deploy(self):
        pass

    def configure(self):
        pass

    def start(self):

        for node in self.nodes:
            ip = node.get('external_IP')
            user = node.get('ssh_user')
            password = node.get("ssh_password")
            name = node.get("hostname")

            logging.info("Starting "+self.service_name+" Service On Node: "+name)
            rsh = RemoteShell(ip, user, password)
            rsh.connect()

            rsh.execute("systemctl daemon-reload")
            output = rsh.execute("systemctl restart "+self.service_name)
            logging.info(output)
            rsh.close()

            if output and "failed" in output[0]:
                return False
            else:
                return True



