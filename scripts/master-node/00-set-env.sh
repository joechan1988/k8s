#!/bin/bash
# SET ENV
#set -x

#-----Set Variables-----
host=`hostname`
export NODE_NAME=$host
export HOSTNAME=$NODE_NAME

export KUBE_APISERVER="https://${MASTER_IP}:6443"
export ETCD_ENDPOINTS="https://${MASTER_IP}:2379"
export FLANNEL_ETCD_PREFIX="/kubernetes/network"
export ETCD_NODES=${NODE_NAME}=https://${MASTER_IP}:2380
mkdir /etc/kubernetes

#------Set /etc/hosts------

cat >> /etc/hosts << EOF
$NODE_IP $host
EOF

#-----Copy binaries-----

echo "------Copy Binary to /usr/bin------"

chmod +x ../bin/*
cp --remove-destination ../bin/* /usr/bin


