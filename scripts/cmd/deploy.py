import os
import logging
import auth
from util import common, cert_tool, config_parser
from templates import constants, json_schema
from util.common import RemoteShell
from util.exception import (PreCheckError, ClusterConfigError, BaseError)
from services import *

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
                    datefmt='%a, %d %b %Y %H:%M:%S',
                    )


def validate_cluster_data(cluster_data):
    """
    Constraints:
    1. control node shouldn't be either labeled as worker node

    :param cluster_data:
    :return:
    """

    # Node Role Check:

    for node in cluster_data.get("nodes"):
        role = node.get('role')
        name = node.get('hostname')
        ip = node.get('external_IP')
        if 'control' in role and 'worker' in role:
            raise ClusterConfigError("Node {0}, IP:{1} is labeled as control and worker at the same time".format(name,ip))


def pre_check(cluster_data, rsh=RemoteShell()):
    """
    Environment check before starting deployment procedure.

    :param cluster_data:  cluster.yml data
    :param rsh:  Remote Shell Obj to connect ssh to node
    :return: result dict
                result:  "passed" or "failed"
                hint: detailed message
    """

    ret = dict({"result": "passed",
                "node": "",
                "hint": ""
                })

    nodes = cluster_data.get("nodes")

    docker_version_cmd = "docker version --format {{.Server.Version}}"
    leftover_dirs_check_list = ["/var/lib/kubelet/",
                                "/etc/kubernetes/"
                                ]

    for node in nodes:
        ip = node.get('external_IP')
        user = node.get('ssh_user')
        password = node.get("ssh_password")
        name = node.get("hostname")

        ret["node"] = "Node IP: " + ip + "; Node Name: " + name

        # SSH Connection Reachability Check

        rsh = RemoteShell(ip, user, password)

        if rsh.connect() == False:
            ret["result"] = "failed"
            ret["hint"] = "Node {" + name + "}, IP: " + ip + " is NOT Reachable, Check SSH Connectivity"
            continue

        # ---Docker Version Check ---
        docker_version = rsh.execute(docker_version_cmd)
        if "1.12" not in docker_version[0]:
            ret["result"] = "failed"
            ret["hint"] = "Incompatible Docker Version On Node: " + name + ", Node IP: " + ip + "; \n"

        # ---Left-over Directories Check ---
        leftover_dirs = list([])
        leftover_dir_names = ""

        for directory in leftover_dirs_check_list:
            out = rsh.execute("ls -l " + directory)
            if "No such file or directory" not in out[0] and "total 0" not in out[-1]:
                leftover_dirs.append(directory)
                leftover_dir_names = leftover_dir_names + directory + ", "

        if len(leftover_dirs):
            ret["result"] = "failed"
            ret["hint"] = ret["hint"] + "Fount Unempty Directories: " + leftover_dir_names + "; "

        # --- IPV4 Forwarding Check ---
        ipv4_forward_check = rsh.execute("sysctl net.ipv4.conf.all.forwarding -b")
        if ipv4_forward_check[0] != "1":
            ret["result"] = "failed"
            ret["hint"] = ret["hint"] + "IPV4 Forwarding Is Disabled; "

        # TODO: Essential module check: systemctl, nslookup ...

        rsh.close()

        return ret


def prep_binaries(path):
    """
    Prepare binaries for local start.
    Could be rpm-installed or ftp downloaded.
    For ftp instance, ftp address and list of binaries should be defined in cluster.yml
    :return:
    """

    configs = config_parser.Config(constants.cluster_cfg_path)
    configs.load()
    dl_path = configs.data.get("binaries").get("download_url")
    bin_list = configs.data.get("binaries").get("list")
    urls = []
    for binary in bin_list:
        urls.append(dl_path + binary)

    common.download_binaries(urls, path)


def deploy(cluster_data=dict()):
    # cluster_cfg_path = constants.cluster_cfg_path
    # configs = config_parser.Config(cluster_cfg_path)
    # configs.load()
    # cluster_data = configs.data

    nodes = cluster_data.get("nodes")

    # prepare temp dir

    cert_tmp_path = constants.tmp_k8s_dir
    bin_tmp_path = constants.tmp_bin_dir

    common.prep_conf_dir(cert_tmp_path, "", clear=True)
    common.prep_conf_dir(bin_tmp_path, "", clear=True)

    #  Generate CA cert to temp directory
    auth.generate_ca_cert(cert_tmp_path)

    # Generate Bootstrap Token to temp directory
    auth.generate_bootstrap_token(cert_tmp_path)

    # prep_binaries() to temp directory

    prep_binaries(bin_tmp_path)

    # Generate k8s & etcd cert files to temp directory

    auth.generate_etcd_cert(cert_tmp_path, cluster_data)
    auth.generate_apiserver_cert(cert_tmp_path, cluster_data)
    auth.generate_admin_kubeconfig(cluster_data)

    # Start deployment process:

    docker = Docker()
    apiserver = Apiserver()
    cmanager = CManager()
    scheduler = Scheduler()
    proxy = Proxy()
    etcd = Etcd()
    kubelet = Kubelet()

    for node in nodes:
        ip = node.get('external_IP')
        user = node.get('ssh_user')
        password = node.get("ssh_password")
        name = node.get("hostname")

        rsh = RemoteShell(ip, user, password)
        rsh.connect()

        # Executing Node Pre-Check
        precheck_result = pre_check(cluster_data, rsh)

        if precheck_result["result"] == "failed":
            raise PreCheckError(precheck_result["hint"])

        if 'etcd' in node.get("role"):
            etcd.remote_shell = rsh
            etcd.node_ip = ip
            etcd.host_name = name
            etcd.tmp_cert_path = cert_tmp_path
            etcd.configure(**cluster_data)
            etcd.deploy()

            etcd.start()

        if 'control' in node.get('role'):
            for service in [docker, apiserver, cmanager, scheduler, kubelet, proxy]:
                service.remote_shell = rsh
                service.node_ip = ip
                service.host_name = name
                service.configure(**cluster_data)
                service.deploy()
                service.start()

        if 'worker' in node.get('role'):
            for service in [docker, kubelet, proxy]:
                service.remote_shell = rsh
                service.node_ip = ip
                service.host_name = name
                service.configure(**cluster_data)
                service.deploy()
                service.start()
