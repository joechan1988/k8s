import os
from util import common, cert_tool, config_parser
from templates import constants, json_schema


def prep_dir():
    common.prep_conf_dir(constants.tmp_etcd_dir, '', clear=True)
    common.prep_conf_dir(constants.tmp_k8s_dir, '', clear=True)


def check_env(**cluster_data):
    # TODO: Docker version check;
    # TODO: Left-over directory check;
    # TODO: IPV4 Forwarding sysctl conf check;

    pass


def generate_admin_kubeconfig():
    # generate admin cert files
    admin_json = json_schema.k8s_admin_csr
    tmp_k8s_dir = constants.tmp_k8s_dir
    csr_file_path = constants.tmp_k8s_dir + "admin-csr.json"

    cert_tool.generate_json_file(csr_file_path, admin_json)
    cert_tool.gen_cert_files(ca_dir=tmp_k8s_dir, profile='kubernetes',
                             csr_file=tmp_k8s_dir + 'admin-csr.json',
                             cert_name='admin',
                             dest_dir=tmp_k8s_dir, debug=constants.debug)

    cmds = []
    cmds.append("kubectl config set-cluster kubernetes \
              --certificate-authority=" + tmp_k8s_dir + "ca.pem \
              --embed-certs=true \
              --server=$1")

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
    configs = config_parser.Config("./cluster.yml")
    configs.load()
    dl_path = configs.data.get("binaries").get("download_url")
    bin_list = configs.data.get("binaries").get("list")
    urls = []
    for binary in bin_list:
        urls.append(dl_path+binary)

    common.download_binaries(urls)


def run():
    # TODO: Generate CA cert
    # TODO: Generate admin kubeconfig file
    # TODO:

    pass
