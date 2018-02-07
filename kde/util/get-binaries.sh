#!/usr/bin/env bash

base_url="ftp://public:123456@joechan1988.asuscomm.com/Other/share/kubernetes/binaries/v1.7.4/server/bin/"
save_path="/tmp/bin/"  # Need to be the same path to cluster.yml

binaries_list=(
kube-apiserver
kubectl
kubelet
kube-controller-manager
etcd
etcdctl
flanneld
mk-docker-opts.sh
kube-scheduler
kube-proxy
cfssl
cfssl-certinfo
cfssljson
)

version_tag=$1
remove_all=$2

#
#if [[ ! -f "/usr/bin/wget" ]]
#then
#  yum install -y wget
#fi
#
## ------cfssl tools-----
#
#if [[ ! -f "/usr/bin/cfssl" || \
# ! -f "/usr/bin/cfssljson" || ! -f "/usr/bin/cfssl-certinfo" ]]
#then
#  wget -c -O /usr/bin/cfssl https://pkg.cfssl.org/R1.2/cfssl_linux-amd64
#  wget -c -O /usr/bin/cfssljson https://pkg.cfssl.org/R1.2/cfssljson_linux-amd64
#  wget -c -O /usr/bin/cfssl-certinfo https://pkg.cfssl.org/R1.2/cfssl-certinfo_linux-amd64
#
#  chmod +x /usr/bin/cfssl
#  chmod +x /usr/bin/cfssljson
#  chmod +x /usr/bin/cfssl-certinfo
#
#fi
#
#
#
#  #---remove previous binaries ----
#if [ ${remove_all} = 'yes' ]
#then
#  for bin in ${binaries_list[@]}
#  do
#    rm -f ${save_path}${bin}
#  done
#fi
#  #-----------------
#
for bin in ${binaries_list[@]}
do
  if [[ ! -f ${save_path}"${bin}" ]]
  then
    wget -c -P ${save_path} \
    ${base_url}${bin}
    chmod +x ${save_path}${bin}
  fi
done



