#!/usr/bin/env bash


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
if [[ ! -f "/usr/bin/kubectl" \
      ||  ! -f "/usr/bin/kube-apiserver"  \
      ||  ! -f "/usr/bin/kube-scheduler"  \
      ||  ! -f "/usr/bin/kube-controller-manager" \
      ||  ! -f "/usr/bin/kube-proxy"   \
      ||  ! -f "/usr/bin/kubelet" \
      ||  ! -f "/usr/bin/kubeadm"  \
      ||  ! -f "/usr/bin/flanneld" \
      ||  ! -f "/usr/bin/etcd" \
       ]]
then
 wget -c -P /usr/bin/ ftp://public:123456@joechan1988.asuscomm.com/Other/share/kubernetes/binaries/v1.7.4/server/bin/kubectl
 wget -c -P /usr/bin/ ftp://public:123456@joechan1988.asuscomm.com/Other/share/kubernetes/binaries/v1.7.4/server/bin/kube-apiserver
 wget -c -P /usr/bin/ ftp://public:123456@joechan1988.asuscomm.com/Other/share/kubernetes/binaries/v1.7.4/server/bin/kube-scheduler
 wget -c -P /usr/bin/ ftp://public:123456@joechan1988.asuscomm.com/Other/share/kubernetes/binaries/v1.7.4/server/bin/kube-controller-manager
 wget -c -P /usr/bin/ ftp://public:123456@joechan1988.asuscomm.com/Other/share/kubernetes/binaries/v1.7.4/server/bin/kube-proxy
 wget -c -P /usr/bin/ ftp://public:123456@joechan1988.asuscomm.com/Other/share/kubernetes/binaries/v1.7.4/server/bin/kubelet
 wget -c -P /usr/bin/ ftp://public:123456@joechan1988.asuscomm.com/Other/share/kubernetes/binaries/v1.7.4/server/bin/kubeadm
 wget -c -P /usr/bin/ ftp://public:123456@joechan1988.asuscomm.com/Other/share/kubernetes/flannel/flanneld
 wget -c -P /usr/bin/ ftp://public:123456@joechan1988.asuscomm.com/Other/share/kubernetes/flannel/mk-docker-opts.sh
 wget -c -P /usr/bin/ ftp://public:123456@joechan1988.asuscomm.com/Other/share/kubernetes/etcd/etcd
 wget -c -P /usr/bin/ ftp://public:123456@joechan1988.asuscomm.com/Other/share/kubernetes/etcd/etcdctl

 chmod +x /usr/bin/kube*
 chmod +x /usr/bin/flanneld
 chmod +x /usr/bin/etcd*

fi

