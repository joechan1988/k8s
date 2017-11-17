#!/usr/bin/env bash

etcd_endpoints=$1
flannel_etcd_prefix=$2
cluster_cidr=$3

etcdctl \
  --endpoints=${etcd_endpoints} \
  --ca-file=/etc/kubernetes/ssl/ca.pem \
  --cert-file=/etc/flanneld/ssl/flanneld.pem \
  --key-file=/etc/flanneld/ssl/flanneld-key.pem \
  set ${flannel_etcd_prefix}/config \
  '{"Network":"'${cluster_cidr}'", "SubnetLen": 24, "Backend": {"Type": "vxlan"}}'