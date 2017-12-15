import os
from util import common, cert_tool, config_parser
from templates import constants, json_schema
from util.common import RemoteShell


def prep_dir():
    common.prep_conf_dir(constants.tmp_etcd_dir, '', clear=True)
    common.prep_conf_dir(constants.tmp_k8s_dir, '', clear=True)


def pre_check(cluster_data, rsh=RemoteShell()):
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

        # TODO: SSH Connection Reachability Check

        rsh = RemoteShell(ip, user, password)

        if rsh.connect()==False:
            ret["result"] = "failed"
            ret["hint"] = "Node {"+name+"}, IP: "+ip+" is NOT Reachable, Check SSH Connectivity"
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


def generate_admin_kubeconfig(**cluster_data):

    # TODO: admin.kubeconfig server should be LB address by default.Set to 1st control node ip

    nodes = cluster_data.get("nodes")
    control_nodes = list([])
    for node in nodes:
        if 'control' in node.get('role'):
            control_nodes.append(node)

    control_node_ip = control_nodes[0].get("external_IP")
    server_url = "https://"+control_node_ip+":6443"

    # generate admin cert files
    admin_json = json_schema.k8s_admin_csr
    tmp_k8s_dir = constants.tmp_k8s_dir
    csr_file_path = constants.tmp_k8s_dir + "admin-csr.json"

    cert_tool.generate_json_file(csr_file_path, admin_json)
    cert_tool.gen_cert_files(ca_dir=tmp_k8s_dir, profile='kubernetes',
                             csr_file=tmp_k8s_dir + 'admin-csr.json',
                             cert_name='admin',
                             dest_dir=tmp_k8s_dir, debug=constants.debug)

    cmds = list([])
    cmds.append("kubectl config set-cluster kubernetes \
              --certificate-authority=" + tmp_k8s_dir + "ca.pem \
              --embed-certs=true \
              --server="+server_url)

    cmds.append("kubectl config set-credentials admin \
              --client-certificate=" + tmp_k8s_dir + "admin.pem \
              --embed-certs=true \
              --client-key=" + tmp_k8s_dir + "admin-key.pem")

    cmds.append("kubectl config set-context kubernetes \
              --cluster=kubernetes \
              --user=admin")

    cmds.append("kubectl config use-context kubernetes")

    cmds.append("cp -f /root/.kube/config " + tmp_k8s_dir + "admin.kubeconfig")

    for cmd in cmds:
        common.shell_exec(cmd, shell=True, debug=constants.debug)


def prep_binaries():
    configs = config_parser.Config(constants.cluster_cfg_path)
    configs.load()
    dl_path = configs.data.get("binaries").get("download_url")
    bin_list = configs.data.get("binaries").get("list")
    urls = []
    for binary in bin_list:
        urls.append(dl_path + binary)

    common.download_binaries(urls, constants.tmp_bin_dir)


def run():

    # TODO: precheck
    # TODO: Generate CA cert
    # TODO: Generate admin kubeconfig file
    # TODO: Generate Bootstrap Token
    # TODO: prep_binaries()

    pass
