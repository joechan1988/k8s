#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import subprocess
import argparse


parser = argparse.ArgumentParser()

#------Args ------

parser.add_argument('--role',dest='node_role',type=str,default='',required=True,help="Node Role Type:master/minion")
args = parser.parse_args()

#------Global Vars------
master_service_list = ['etcd','kube-apiserver',
                'kube-controller-manager','kube-scheduler']
node_service_list = ['flanneld','docker','kubelet','kube-proxy']
success_list =[]
failed_list = []

role = args.node_role

#------Funcs ------

def start_service(service_name):
    print("------Starting Service: %s"% service_name)
    output = subprocess.check_output(["systemctl","restart",service_name])

    if 'failed' in output:
        failed_list.append(service_name)
    else:
        success_list.append(service_name)


#------ Start Service ------

if args.node_role == 'master':
    for service in master_service_list:
        start_service(service)
    subprocess.call(["kubectl", "apply", "-f", "../addons/csr-auto-approve.yml"])
    for service in node_service_list:
        start_service(service)

    print('Successfully Start Service: %s' % success_list)
    print('Failed to Start: %s' % failed_list)

else:
    for service in node_service_list:
        start_service(service)

    print('Successfully Start Service: %s' % success_list)
    print('Failed to Start: %s' % failed_list)