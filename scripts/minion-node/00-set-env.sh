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

#-------Clean Env-------
read -t 30 -p "Clean OS Environment Before Deploying? [yN]" judge
if [[ $judge == 'y' ]]
then
  echo "Cleaning OS Environment"
  systemctl disable kubelet.service
  systemctl disable kube-apiserver.service
  systemctl disable kube-proxy.service
  systemctl disable kube-scheduler.service
  systemctl disable kube-controller-manager.service
  systemctl disable etcd.service

  rm -rf /etc/systemd/system/docker.service
  rm -rf /etc/systemd/system/docker.service.d/*
  rm -rf /etc/systemd/system/kubelet.service
  rm -rf /etc/systemd/system/kubelet.service.d/*
  rm -rf /etc/systemd/system/kube-apiserver.service
  rm -rf /etc/systemd/system/kube-scheduler.service
  rm -rf /etc/systemd/system/kube-controller-manager.service
  rm -rf /etc/systemd/system/kube-proxy.service
  rm -rf /etc/systemd/system/etcd.service
  rm -rf /var/lib/kubelet/*
fi


#-----Copy binaries-----

echo "------Copy Binary to /usr/bin------"

chmod +x ../bin/*
cp --remove-destination ../bin/* /usr/bin


