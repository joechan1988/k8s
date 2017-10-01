#!/usr/bin/env bash

version_tag=$1
remove_all=$2


if [[ ! -f "/usr/bin/wget" ]]
then
  yum install -y wget
fi

# ------cfssl tools-----

if [[ ! -f "/usr/bin/cfssl" || \
 ! -f "/usr/bin/cfssljson" || ! -f "/usr/bin/cfssl-certinfo" ]]
then
  wget -c -O /usr/bin/cfssl https://pkg.cfssl.org/R1.2/cfssl_linux-amd64 -O cfssl -P /usr/bin/
  wget -c -O /usr/bin/cfssljson https://pkg.cfssl.org/R1.2/cfssljson_linux-amd64
  wget -c -O /usr/bin/cfssl-certinfo https://pkg.cfssl.org/R1.2/cfssl-certinfo_linux-amd64

  chmod +x /usr/bin/cfssl
  chmod +x /usr/bin/cfssljson
  chmod +x /usr/bin/cfssl-certinfo

fi



#------kubernetes binaries ------

k8s_binaries=(kubectl \
            kube-apiserver \
            kube-scheduler \
            kube-controller-manager\
            kube-proxy\
            kubelet \
            kubeadm \
            )

  #---remove previous binaries ----
if [ ${remove_all} = 'yes' ]
then
  for bin in ${k8s_binaries[@]}
  do
    rm -f /usr/bin/${bin}
  done
fi
  #-----------------

for bin in ${k8s_binaries[@]}
do
  if [[ ! -f "/usr/bin/${bin}" ]]
  then
    wget -c -P /usr/bin/ \
    ftp://public:123456@joechan1988.asuscomm.com/Other/share/kubernetes/binaries/${version_tag}/server/bin/${bin}
  fi
done


#------Flannel&&etcd binaries ------

if [[ ! -f "/usr/bin/flanneld" ||  ! -f "/usr/bin/etcd" ]]
then
 wget -c -P /usr/bin/ ftp://public:123456@joechan1988.asuscomm.com/Other/share/kubernetes/flannel/flanneld
 wget -c -P /usr/bin/ ftp://public:123456@joechan1988.asuscomm.com/Other/share/kubernetes/flannel/mk-docker-opts.sh
 wget -c -P /usr/bin/ ftp://public:123456@joechan1988.asuscomm.com/Other/share/kubernetes/etcd/etcd
 wget -c -P /usr/bin/ ftp://public:123456@joechan1988.asuscomm.com/Other/share/kubernetes/etcd/etcdctl
fi

chmod +x /usr/bin/kube*
chmod +x /usr/bin/flanneld
chmod +x /usr/bin/mk-docker-opts.sh
chmod +x /usr/bin/etcd*


