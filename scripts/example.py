#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals  # We require Python 2.6 or later
from string import Template
import random
import string
import os
import sys
import argparse
import subprocess
import shutil
import base64
from io import open

if sys.version_info[:3][0] == 2:
    import ConfigParser as ConfigParser
    import StringIO as StringIO

if sys.version_info[:3][0] == 3:
    import configparser as ConfigParser
    import io as StringIO


def validate(conf, args):
    protocol = rcp.get("configuration", "ui_url_protocol")
    if protocol != "https" and args.notary_mode:
        raise Exception("Error: the protocol must be https when Harbor is deployed with Notary")
    if protocol == "https":
        if not rcp.has_option("configuration", "ssl_cert"):
            raise Exception("Error: The protocol is https but attribute ssl_cert is not set")
        cert_path = rcp.get("configuration", "ssl_cert")
        if not os.path.isfile(cert_path):
            raise Exception("Error: The path for certificate: %s is invalid" % cert_path)
        if not rcp.has_option("configuration", "ssl_cert_key"):
            raise Exception("Error: The protocol is https but attribute ssl_cert_key is not set")
        cert_key_path = rcp.get("configuration", "ssl_cert_key")
        if not os.path.isfile(cert_key_path):
            raise Exception("Error: The path for certificate key: %s is invalid" % cert_key_path)
    project_creation = rcp.get("configuration", "project_creation_restriction")

    if project_creation != "everyone" and project_creation != "adminonly":
        raise Exception("Error invalid value for project_creation_restriction: %s" % project_creation)


def get_secret_key(path):
    secret_key = _get_secret(path, "secretkey")
    if len(secret_key) != 16:
        raise Exception("secret key's length has to be 16 chars, current length: %d" % len(secret_key))
    return secret_key


def get_alias(path):
    alias = _get_secret(path, "defaultalias", length=8)
    return alias


def _get_secret(folder, filename, length=16):
    key_file = os.path.join(folder, filename)
    if os.path.isfile(key_file):
        with open(key_file, 'r') as f:
            key = f.read()
            print("loaded secret from file: %s" % key_file)
        return key
    if not os.path.isdir(folder):
        os.makedirs(folder, mode=0600)
    key = ''.join(random.choice(string.ascii_letters + string.digits) for i in range(length))
    with open(key_file, 'w') as f:
        f.write(key)
        print("Generated and saved secret to file: %s" % key_file)
    os.chmod(key_file, 0600)
    return key


def prep_conf_dir(root, name):
    absolute_path = os.path.join(root, name)
    if not os.path.exists(absolute_path):
        os.makedirs(absolute_path)
    return absolute_path


def render(src, dest, **kw):
    t = Template(open(src, 'r').read())
    if not os.path.exists(dest):
        os.mknod(dest)
    with open(dest, 'w') as f:
        f.write(t.substitute(**kw))
    print("Generated configuration file: %s" % dest)


base_dir = os.path.dirname(__file__)
config_dir = os.path.join(base_dir, "k8s_yaml")
templates_dir = os.path.join(base_dir, "templates")
FNULL = open(os.devnull, 'w')

def delfile(src):
    if os.path.isfile(src):
        try:
            os.remove(src)
            print("Clearing the configuration file: %s" % src)
        except:
            pass
    elif os.path.isdir(src):
        for item in os.listdir(src):
            itemsrc = os.path.join(src, item)
            delfile(itemsrc)



def cfssl_installed():
    shell_stat = subprocess.check_call(["which", "cfssl"], stdout=FNULL, stderr=subprocess.STDOUT)
    if shell_stat != 0:
        print("Cannot find cfssl installed in this computer\nUse default SSL certificate file")
        return False
    return True


parser = argparse.ArgumentParser()
parser.add_argument('--conf', dest='cfgfile', default=base_dir + '/harbor.cfg', type=str,
                    help="the path of Harbor configuration file")
parser.add_argument('--with-notary', dest='notary_mode', default=False, action='store_true',
                    help="the Harbor instance is to be deployed with notary")
parser.add_argument('--with-clair', dest='clair_mode', default=False, action='store_true',
                    help="the Harbor instance is to be deployed with clair")
parser.add_argument('--test',dest='test_unit',type=str,default='')
args = parser.parse_args()

delfile(config_dir)
# Read configurations
conf = StringIO.StringIO()
conf.write("[configuration]\n")
conf.write(open(args.cfgfile).read())
conf.seek(0, os.SEEK_SET)
rcp = ConfigParser.RawConfigParser()
rcp.readfp(conf)

validate(rcp, args)

host_ip = rcp.get("configuration", "host_ip")
hostname = rcp.get("configuration", "hostname")
cluster_ip = rcp.get("configuration", "cluster_ip")
service_port = rcp.get("configuration", "service_port")
protocol = rcp.get("configuration", "ui_url_protocol")
ui_url = protocol + "://" + cluster_ip
ext_ui_url = protocol + "://" + host_ip
email_identity = rcp.get("configuration", "email_identity")
email_host = rcp.get("configuration", "email_server")
email_port = rcp.get("configuration", "email_server_port")
email_usr = rcp.get("configuration", "email_username")
email_pwd = rcp.get("configuration", "email_password")
email_from = rcp.get("configuration", "email_from")
email_ssl = rcp.get("configuration", "email_ssl")
harbor_admin_password = rcp.get("configuration", "harbor_admin_password")
auth_mode = rcp.get("configuration", "auth_mode")
ldap_url = rcp.get("configuration", "ldap_url")
# this two options are either both set or unset
if rcp.has_option("configuration", "ldap_searchdn"):
    ldap_searchdn = rcp.get("configuration", "ldap_searchdn")
    ldap_search_pwd = rcp.get("configuration", "ldap_search_pwd")
else:
    ldap_searchdn = ""
    ldap_search_pwd = ""
ldap_basedn = rcp.get("configuration", "ldap_basedn")
# ldap_filter is null by default
if rcp.has_option("configuration", "ldap_filter"):
    ldap_filter = rcp.get("configuration", "ldap_filter")
else:
    ldap_filter = ""
ldap_uid = rcp.get("configuration", "ldap_uid")
ldap_scope = rcp.get("configuration", "ldap_scope")
ldap_timeout = rcp.get("configuration", "ldap_timeout")
db_password = rcp.get("configuration", "db_password")
self_registration = rcp.get("configuration", "self_registration")
if protocol == "https":
    cert_path = rcp.get("configuration", "ssl_cert")
    cert_key_path = rcp.get("configuration", "ssl_cert_key")
customize_crt = rcp.get("configuration", "customize_crt")
max_job_workers = rcp.get("configuration", "max_job_workers")
token_expiration = rcp.get("configuration", "token_expiration")
verify_remote_cert = rcp.get("configuration", "verify_remote_cert")
proj_cre_restriction = rcp.get("configuration", "project_creation_restriction")
secretkey_path = rcp.get("configuration", "secretkey_path")
clair_db_password = rcp.get("configuration", "clair_db_password")
if rcp.has_option("configuration", "admiral_url"):
    admiral_url = rcp.get("configuration", "admiral_url")
else:
    admiral_url = ""
pg_password = rcp.get("configuration", "clair_db_password")
secret_key = get_secret_key(secretkey_path)
########

ui_secret = ''.join(random.choice(string.ascii_letters + string.digits) for i in range(16))
jobservice_secret = ''.join(random.choice(string.ascii_letters + string.digits) for i in range(16))

adminserver_config_dir = os.path.join(config_dir, "adminserver")
# if not os.path.exists(adminserver_config_dir):
#     os.makedirs(os.path.join(config_dir, "adminserver"))

# ui_config_dir = prep_conf_dir(config_dir, "ui")
# db_config_dir = prep_conf_dir(config_dir, "db")
# job_config_dir = prep_conf_dir(config_dir, "jobservice")
# registry_config_dir = prep_conf_dir(config_dir, "registry")
# nginx_config_dir = prep_conf_dir(config_dir, "nginx")
# nginx_conf_d = prep_conf_dir(nginx_config_dir, "conf.d")

cm_config_dir = prep_conf_dir(config_dir,"cm")
secret_config_dir =prep_conf_dir(config_dir,"secret")
# dpl_config_dir = prep_conf_dir(config_dir,"deployment")
cert_config_dir = prep_conf_dir(config_dir,"cert")


# pvc_config_dir = prep_conf_dir(config_dir,"pvc")
# svc_config_dir = prep_conf_dir(config_dir,"svc")

adminserver_cm = os.path.join(config_dir, "cm","adminserver-cm.yaml")
adminserver_secret = os.path.join(config_dir, "secret","adminserver-secrets.yaml")

ui_cm = os.path.join(config_dir, "cm", "ui-cm.yaml")
ui_secret = os.path.join(config_dir, "secret", "ui-secrets.yaml")

jobservice_cm = os.path.join(config_dir, "cm", "jobservice-cm.yaml")
jobservice_secret_path = os.path.join(config_dir, "secret", "jobservice-secrets.yaml")

registry_cm = os.path.join(config_dir, "cm", "registry-cm.yaml")
registry_secret = os.path.join(config_dir, "secret", "registry-secrets.yaml")

mysql_secret = os.path.join(config_dir, "secret", "mysql-secrets.yaml")

nginx_cm = os.path.join(config_dir,"cm", "nginx-cm.yaml")
nginx_secret = os.path.join(config_dir,"secret", "nginx-secrets.yaml")

clair_cm = os.path.join(config_dir,"cm", "clair-cm.yaml")
postgres_secret = os.path.join(config_dir,"secret", "postgres-secrets.yaml")

cert_dir = os.path.join(config_dir, "cert")


render(os.path.join(templates_dir, "cert", "harbor.json"),
       os.path.join(cert_dir,"harbor.json"),
       host_ip=host_ip,hostname=hostname,cluster_ip=cluster_ip
       )

if cfssl_installed():
    if not os.path.exists(cert_dir):
        os.makedirs(cert_dir)
    # shutil.copyfile(os.path.join(templates_dir, "cert", "generate_cert.sh"),
    #                 os.path.join(cert_dir,"generate_cert.sh"))
    shutil.copyfile(os.path.join(templates_dir, "cert", "ca-config.json"),
                    os.path.join(cert_dir, "ca-config.json"))
    shutil.copyfile(os.path.join(templates_dir, "cert", "ca-csr.json"),
                    os.path.join(cert_dir, "ca-csr.json"))

    subprocess.call(["bash","-c","./generate_cert.sh"],
                    )
    # subprocess.call(["cd","-"],stdout=FNULL,
    #                 stderr=subprocess.STDOUT)
    # subprocess.call(["cfssl","gencert","-initca",os.path.join(cert_dir,"ca-csr.json"),"|","cfssljson", "-bare", "ca", "-"])


# render(os.path.join(templates_dir, "cm","nginx-cm.yaml"),nginx_cm)

shutil.copyfile(os.path.join(templates_dir, "cm", "nginx-cm.yaml"), nginx_cm)

render(os.path.join(templates_dir, "secret", "adminserver-secrets.yaml"),
       adminserver_secret,
       secret_key=base64.b64encode(secret_key),
       ldap_search_pwd=base64.b64encode(ldap_search_pwd),
       harbor_admin_password=base64.b64encode(harbor_admin_password),
       clair_db_password=base64.b64encode(clair_db_password),
       email_pwd=base64.b64encode(email_pwd),
       )

render(os.path.join(templates_dir, "cm", "adminserver-cm.yaml"),
       adminserver_cm,
       ui_url=ext_ui_url,
       auth_mode=auth_mode,
       self_registration=self_registration,
       ldap_url=ldap_url,
       ldap_searchdn=ldap_searchdn,
       ldap_basedn=ldap_basedn,
       ldap_filter=ldap_filter,
       ldap_uid=ldap_uid,
       ldap_scope=ldap_scope,
       ldap_timeout=ldap_timeout,
       db_password=db_password,
       email_host=email_host,
       email_port=email_port,
       email_usr=email_usr,
       email_ssl=email_ssl,
       email_from=email_from,
       email_identity=email_identity,
       project_creation_restriction=proj_cre_restriction,
       verify_remote_cert=verify_remote_cert,
       max_job_workers=max_job_workers,
       ui_secret=ui_secret,
       jobservice_secret=jobservice_secret,
       token_expiration=token_expiration,
       admiral_url=admiral_url,
       with_notary=args.notary_mode,
       with_clair=args.clair_mode,
       pg_password=pg_password
       )

render(os.path.join(templates_dir, "cm", "ui-cm.yaml"),ui_cm)
render(os.path.join(templates_dir, "secret", "ui-secrets.yaml"),
       ui_secret,
       secret_key=base64.b64encode(secret_key),
       ui_secret=base64.b64encode(ui_secret)
       )

render(os.path.join(templates_dir, "cm",
                    "registry-cm.yaml"),
       registry_cm,
       ui_url=ui_url)
render(os.path.join(templates_dir, "secret", "registry-secrets.yaml"),
       registry_secret)

#
# render(os.path.join(templates_dir, "secret",
#                     "registry-secrets.yaml"),
#        registry_cm,
#        ui_url=ui_url)

render(os.path.join(templates_dir, "secret", "mysql-secrets.yaml"),
       mysql_secret,
       db_password=base64.b64encode(db_password))

render(os.path.join(templates_dir, "cm", "jobservice-cm.yaml"),
       jobservice_cm)
render(os.path.join(templates_dir, "secret", "jobservice-secrets.yaml"),
       jobservice_secret_path,
       secret_key=base64.b64encode(secret_key),
       jobservice_secret=base64.b64encode(jobservice_secret))

render(os.path.join(templates_dir, "secret", "postgres-secrets.yaml"),
       postgres_secret,
        clair_db_password=base64.b64encode(clair_db_password))

render(os.path.join(templates_dir, "cm", "clair-cm.yaml"),
       clair_cm,
        clair_db_password=clair_db_password)


#
# print("Generated configuration file: %s" % jobservice_conf)
if os.path.exists(os.path.join(config_dir,"service")) or \
    os.path.exists(os.path.join(config_dir, "pvc")) or \
    os.path.exists(os.path.join(config_dir, "deployment")):
    shutil.rmtree(os.path.join(config_dir,"service"))
    shutil.rmtree(os.path.join(config_dir,"pvc"))
    shutil.rmtree(os.path.join(config_dir,"deployment"))
shutil.copytree(os.path.join(templates_dir, "service"),
                os.path.join(config_dir,"service"))
shutil.copytree(os.path.join(templates_dir, "pvc"),
                os.path.join(config_dir,"pvc"))
shutil.copytree(os.path.join(templates_dir, "deployment"),
                os.path.join(config_dir,"deployment"))

render(os.path.join(templates_dir, "service", "nginx-svc.yaml"),
       service_port=service_port,
       cluster_ip=cluster_ip)
#
# print("Generated configuration file: %s" % ui_conf)
# shutil.copyfile(os.path.join(templates_dir, "cm", "ui.yaml"), ui_conf)


def validate_crt_subj(dirty_subj):
    subj_list = [item for item in dirty_subj.strip().split("/") \
                 if len(item.split("=")) == 2 and len(item.split("=")[1]) > 0]
    return "/" + "/".join(subj_list)




from functools import wraps


def stat_decorator(func):
    @wraps(func)
    def check_wrapper(*args, **kw):
        stat = func(*args, **kw)
        message = "Generated certificate, key file: %s, cert file: %s" % (kw['key_path'], kw['cert_path']) \
            if stat == 0 else "Fail to generate key file: %s, cert file: %s" % (kw['key_path'], kw['cert_path'])
        print(message)
        if stat != 0:
            sys.exit(1)

    return check_wrapper


@stat_decorator
def create_root_cert(subj, key_path="./k.key", cert_path="./cert.crt"):
    rc = subprocess.call(["openssl", "genrsa", "-out", key_path, "4096"], stdout=FNULL, stderr=subprocess.STDOUT)
    if rc != 0:
        return rc
    return subprocess.call(["openssl", "req", "-new", "-x509", "-key", key_path, \
                            "-out", cert_path, "-days", "3650", "-subj", subj], stdout=FNULL, stderr=subprocess.STDOUT)


@stat_decorator
def create_cert(subj, ca_key, ca_cert, key_path="./k.key", cert_path="./cert.crt"):
    cert_dir = os.path.dirname(cert_path)
    csr_path = os.path.join(cert_dir, "tmp.csr")
    rc = subprocess.call(["openssl", "req", "-newkey", "rsa:4096", "-nodes", "-sha256", "-keyout", key_path, \
                          "-out", csr_path, "-subj", subj], stdout=FNULL, stderr=subprocess.STDOUT)
    if rc != 0:
        return rc
    return subprocess.call(["openssl", "x509", "-req", "-days", "3650", "-in", csr_path, "-CA", \
                            ca_cert, "-CAkey", ca_key, "-CAcreateserial", "-out", cert_path], stdout=FNULL,
                           stderr=subprocess.STDOUT)


def openssl_installed():
    shell_stat = subprocess.check_call(["which", "openssl"], stdout=FNULL, stderr=subprocess.STDOUT)
    if shell_stat != 0:
        print("Cannot find openssl installed in this computer\nUse default SSL certificate file")
        return False
    return True


#
# if customize_crt == 'on' and openssl_installed():
#     shell_stat = subprocess.check_call(["which", "openssl"], stdout=FNULL, stderr=subprocess.STDOUT)
#     empty_subj = "/C=/ST=/L=/O=/CN=/"
#     private_key_pem = os.path.join(config_dir, "ui", "private_key.pem")
#     root_crt = os.path.join(config_dir, "registry", "root.crt")
#     create_root_cert(empty_subj, key_path=private_key_pem, cert_path=root_crt)
#     os.chmod(private_key_pem, 0600)
#     os.chmod(root_crt, 0600)
# else:
#     print("Copied configuration file: %s" % ui_config_dir + "private_key.pem")
#     shutil.copyfile(os.path.join(templates_dir, "ui", "private_key.pem"),
#                     os.path.join(ui_config_dir, "private_key.pem"))
#     print("Copied configuration file: %s" % registry_config_dir + "root.crt")
#     shutil.copyfile(os.path.join(templates_dir, "registry", "root.crt"), os.path.join(registry_config_dir, "root.crt"))
#
if args.notary_mode:
    notary_config_dir = prep_conf_dir(config_dir, "notary")
    notary_temp_dir = os.path.join(templates_dir, "notary")
    print("Copying sql file for notary DB")
    if os.path.exists(os.path.join(notary_config_dir, "mysql-initdb.d")):
        shutil.rmtree(os.path.join(notary_config_dir, "mysql-initdb.d"))
    shutil.copytree(os.path.join(notary_temp_dir, "mysql-initdb.d"), os.path.join(notary_config_dir, "mysql-initdb.d"))
    if customize_crt == 'on' and openssl_installed():
        try:
            temp_cert_dir = os.path.join(base_dir, "cert_tmp")
            if not os.path.exists(temp_cert_dir):
                os.makedirs(temp_cert_dir)
            ca_subj = "/C=US/ST=California/L=Palo Alto/O=VMware, Inc./OU=Harbor/CN=Self-signed by VMware, Inc."
            cert_subj = "/C=US/ST=California/L=Palo Alto/O=VMware, Inc./OU=Harbor/CN=notarysigner"
            signer_ca_cert = os.path.join(temp_cert_dir, "notary-signer-ca.crt")
            signer_ca_key = os.path.join(temp_cert_dir, "notary-signer-ca.key")
            signer_cert_path = os.path.join(temp_cert_dir, "notary-signer.crt")
            signer_key_path = os.path.join(temp_cert_dir, "notary-signer.key")
            create_root_cert(ca_subj, key_path=signer_ca_key, cert_path=signer_ca_cert)
            create_cert(cert_subj, signer_ca_key, signer_ca_cert, key_path=signer_key_path, cert_path=signer_cert_path)
            print("Copying certs for notary signer")
            os.chmod(signer_cert_path, 0600)
            os.chmod(signer_key_path, 0600)
            os.chmod(signer_ca_cert, 0600)
            shutil.copy2(signer_cert_path, notary_config_dir)
            shutil.copy2(signer_key_path, notary_config_dir)
            shutil.copy2(signer_ca_cert, notary_config_dir)
        finally:
            srl_tmp = os.path.join(os.getcwd(), ".srl")
            if os.path.isfile(srl_tmp):
                os.remove(srl_tmp)
            if os.path.isdir(temp_cert_dir):
                shutil.rmtree(temp_cert_dir, True)
    else:
        print("Copying certs for notary signer")
        shutil.copy2(os.path.join(notary_temp_dir, "notary-signer.crt"), notary_config_dir)
        shutil.copy2(os.path.join(notary_temp_dir, "notary-signer.key"), notary_config_dir)
        shutil.copy2(os.path.join(notary_temp_dir, "notary-signer-ca.crt"), notary_config_dir)
    shutil.copy2(os.path.join(registry_cm, "root.crt"), notary_config_dir)
    print("Copying notary signer configuration file")
    shutil.copy2(os.path.join(notary_temp_dir, "signer-config.json"), notary_config_dir)
    render(os.path.join(notary_temp_dir, "server-config.json"),
           os.path.join(notary_config_dir, "server-config.json"),
           token_endpoint=ui_url)

    print("Copying nginx configuration file for notary")
    shutil.copy2(os.path.join(templates_dir, "nginx", "notary.upstream.conf"), nginx_conf_d)
    render(os.path.join(templates_dir, "nginx", "notary.server.conf"),
           os.path.join(nginx_cm, "notary.server.conf"),
           ssl_cert=os.path.join("/etc/nginx/cert", os.path.basename(target_cert_path)),
           ssl_cert_key=os.path.join("/etc/nginx/cert", os.path.basename(target_cert_key_path)))

    default_alias = get_alias(secretkey_path)
    render(os.path.join(notary_temp_dir, "signer_env"), os.path.join(notary_config_dir, "signer_env"),
           alias=default_alias)

if args.clair_mode:
    clair_temp_dir = os.path.join(templates_dir, "clair")
    clair_config_dir = prep_conf_dir(config_dir, "clair")
    if os.path.exists(os.path.join(clair_config_dir, "postgresql-init.d")):
        print("Copying offline data file for clair DB")
        shutil.rmtree(os.path.join(clair_config_dir, "postgresql-init.d"))
    shutil.copytree(os.path.join(clair_temp_dir, "postgresql-init.d"),
                    os.path.join(clair_config_dir, "postgresql-init.d"))
    postgres_env = os.path.join(clair_config_dir, "postgres_env")
    render(os.path.join(clair_temp_dir, "postgres_env"), postgres_env, password=pg_password)
    clair_conf = os.path.join(clair_config_dir, "config.yaml")
    render(os.path.join(clair_temp_dir, "config.yaml"), clair_conf, password=pg_password)

FNULL.close()
print("The configuration files are ready, please start the service.")
