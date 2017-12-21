import os
import logging
import auth
from kde.util import common, cert_tool, config_parser
from kde.templates import constants, json_schema
from kde.util.common import RemoteShell
from kde.util.exception import (PreCheckError, ClusterConfigError, BaseError)
from kde.services import *


#
# logging.basicConfig(level=logging.INFO,
#                     format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
#                     datefmt='%a, %d %b %Y %H:%M:%S',
#                     )


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
            raise ClusterConfigError(
                "Node {0}, IP:{1} is labeled as control and worker at the same time".format(name, ip))


def pre_check(cluster_data):
    """
    Environment check before starting deployment procedure.

    :param cluster_data:  cluster.yml data
    :param rsh:  Remote Shell Obj to connect ssh to node
    :return: result dict
                result:  "passed" or "failed"
                hint: detailed message
    """

    summary = dict({"result": "passed",
                    "node": "",
                    "hint": ""
                    })

    nodes = cluster_data.get("nodes")

    docker_version_cmd = "docker version --format {{.Server.Version}}"
    leftover_dirs_check_list = ["/var/lib/kubelet/",
                                "/etc/kubernetes/",
                                "/var/lib/etcd/"
                                ]

    for node in nodes:
        ip = node.get('external_IP')
        user = node.get('ssh_user')
        password = node.get("ssh_password")
        name = node.get("hostname")

        summary["node"] = "Node IP: " + ip + "; Node Name: " + name

        # SSH Connection Reachability Check
        rsh = RemoteShell(ip, user, password)
        if rsh.connect() == False:
            summary["result"] = "failed"
            summary["hint"] = "Node {" + name + "}(IP: " + ip + ") is NOT reachable. Check SSH connectivity"
            continue

        # ---Docker Version Check ---
        docker_version = rsh.execute(docker_version_cmd)
        if "1.12" not in docker_version[0]:
            summary["result"] = "failed"
            summary["hint"] = "Incompatible Docker version on node: " + name + ", Node IP: " + ip + "; \n"
        if "Cannot connect to the Docker daemon" in docker_version[0]:
            summary["result"] = "failed"
            summary["hint"] = "Docker daemon may not running On node: " + name + ", Node IP: " + ip + "; \n"

        # ---Left-over Directories Check ---
        leftover_dirs = list([])
        leftover_dir_names = ""

        for directory in leftover_dirs_check_list:
            out = rsh.execute("ls -l " + directory)
            if "No such file or directory" not in out[0] and "total 0" not in out[-1]:
                leftover_dirs.append(directory)
                leftover_dir_names = leftover_dir_names + directory + ", "

        if len(leftover_dirs):
            summary["result"] = "failed"
            summary["hint"] = summary["hint"] + "Fount Unempty Directories: " + leftover_dir_names + "; "

        # --- IPV4 Forwarding Check ---
        ipv4_forward_check = rsh.execute("sysctl net.ipv4.conf.all.forwarding -b")
        if ipv4_forward_check[0] != "1":
            summary["result"] = "failed"
            summary["hint"] = summary["hint"] + "IPV4 Forwarding Is Disabled; "

        # TODO: Essential module check: systemctl, nslookup ...

        rsh.close()

        if summary["result"] == "failed":
            raise PreCheckError(summary["hint"])


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


def _deploy_node(ip, user, password, hostname, service_list, **cluster_data):
    rsh = RemoteShell(ip, user, password)
    rsh.connect()

    result = {
        "node": hostname,
        "ip": ip,
        "result":"",
        "failed_service":[]
    }

    for service in service_list:
        service.remote_shell = rsh
        service.node_ip = ip
        service.host_name = hostname
        service.configure(**cluster_data)
        service.deploy()
        ret = service.start()
        if not ret:
            result["failed_service"].append(service.service_name)

    if len(result["failed_service"]) != 0:
        result["result"] = "failure"
    else:
        result["result"] = "success"

    rsh.close()

    return result


def do(cluster_data):
    # TODO: Deployment procedure: all control node failed,stop procedure
    # TODO: deployment order: etcd node > control node > worker node
    # TODO: result notification
    # TODO: depart deploy action to single method
    # TODO: deal with deploy procedure Exception

    results = {
        "summary": "failure",  # success or failure
        "nodes": [
            # {
                #     "node_name": "",
                #     "node_ip": "",
                #     "result": "failure"
            # }
        ]
    }

    try:
        validate_cluster_data(cluster_data)
        pre_check(cluster_data)
    except BaseError as e:
        logging.error(e.message)
        return

    # Prepare local temp directory

    cert_tmp_path = constants.tmp_kde_dir
    common.prep_conf_dir(cert_tmp_path, "", clear=True)
    common.prep_conf_dir(constants.tmp_etcd_dir, "", clear=True)

    # Group node by control and worker
    control_nodes = list()
    worker_nodes = list()
    etcd_nodes = list()
    nodes = cluster_data.get("nodes")
    for node in nodes:
        if "control" in node.get('role'):
            control_nodes.append(node)
        if "worker" in node.get('role'):
            worker_nodes.append(node)
        if "etcd" in node.get('role'):
            etcd_nodes.append(node)


    #  Generate CA cert to temp directory
    auth.generate_ca_cert(cert_tmp_path)

    # Generate Bootstrap Token to temp directory
    auth.generate_bootstrap_token(cert_tmp_path)

    # Prepare binaries to temp directory

    # common.prep_conf_dir(constants.tmp_bin_dir, "", clear=True)
    # prep_binaries(constants.tmp_bin_dir)

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

    def _sum_results(results_dict):
        for item in results_dict["nodes"]:
            if item["result"] == "failure":
                results_dict["summary"] = "failure"
                break
        results_dict["summary"] = "success"

        # Attempt to deploy etcd node
    for node in etcd_nodes:
        ip = node.get('external_IP')
        user = node.get('ssh_user')
        password = node.get("ssh_password")
        name = node.get("hostname")

        service_list = [etcd]
        result = _deploy_node(ip, user, password, name, service_list, **cluster_data)
        results["nodes"].append(result)

        # Summary Etcd node deploy results.If failure, stop the whole deployment
    _sum_results(results)
    if results["summary"] == "failure":
        return results

        # Attempt to deploy controller node
    for node in control_nodes:
        ip = node.get('external_IP')
        user = node.get('ssh_user')
        password = node.get("ssh_password")
        name = node.get("hostname")

        service_list = [docker, apiserver, cmanager, scheduler, kubelet, proxy]
        result = _deploy_node(ip, user, password, name, service_list, **cluster_data)
        results["nodes"].append(result)

        # Summary controller node deploy results.If failure, stop the whole deployment
    _sum_results(results)
    if results["summary"] == "failure":
        return results

        # Attempt to deploy worker node
    for node in worker_nodes:
        ip = node.get('external_IP')
        user = node.get('ssh_user')
        password = node.get("ssh_password")
        name = node.get("hostname")

        service_list = [docker, kubelet, proxy]
        result = _deploy_node(ip, user, password, name, service_list, **cluster_data)
        results["nodes"].append(result)

    _sum_results(results)

        # for node in nodes:
        #     ip = node.get('external_IP')
        #     user = node.get('ssh_user')
        #     password = node.get("ssh_password")
        #     name = node.get("hostname")
        #
        #     rsh = RemoteShell(ip, user, password)
        #     rsh.connect()
        #
        #     # Executing Node Pre-Check
        #     precheck_result = pre_check(cluster_data, rsh)
        #
        #     if precheck_result["result"] == "failed":
        #         raise PreCheckError(precheck_result["hint"])
        #
        #     if 'etcd' in node.get("role"):
        #         etcd.remote_shell = rsh
        #         etcd.node_ip = ip
        #         etcd.host_name = name
        #         etcd.tmp_cert_path = cert_tmp_path
        #         etcd.configure(**cluster_data)
        #         etcd.deploy()
        #
        #         etcd.start()
        #
        #     if 'control' in node.get('role'):
        #         for service in [docker, apiserver, cmanager, scheduler, kubelet, proxy]:
        #             service.remote_shell = rsh
        #             service.node_ip = ip
        #             service.host_name = name
        #             service.configure(**cluster_data)
        #             service.deploy()
        #             service.start()
        #
        #     if 'worker' in node.get('role'):
        #         for service in [docker, kubelet, proxy]:
        #             service.remote_shell = rsh
        #             service.node_ip = ip
        #             service.host_name = name
        #             service.configure(**cluster_data)
        #             service.deploy()
        #             service.start()

    return results


def join():
    """
    Join a existing kubernetes cluster

    :return:
    """
    pass
