#!/bin/bash

#set -x

#Generate CA files

mkdir -p /etc/kubernetes/ssl

cat > /etc/kubernetes/ssl/ca-config.json <<EOF
{
  "signing": {
    "default": {
      "expiry": "8760h"
    },
    "profiles": {
      "kubernetes": {
        "usages": [
            "signing",
            "key encipherment",
            "server auth",
            "client auth"
        ],
        "expiry": "8760h"
      }
    }
  }
}
EOF

cat > /etc/kubernetes/ssl/ca-csr.json <<EOF
{
  "CN": "kubernetes",
  "key": {
    "algo": "rsa",
    "size": 2048
  },
  "names": [
    {
      "C": "CN",
      "ST": "BeiJing",
      "L": "BeiJing",
      "O": "k8s",
      "OU": "System"
    }
  ]
}
EOF

cfssl gencert -initca /etc/kubernetes/ssl/ca-csr.json | cfssljson -bare ca
mv ca* /etc/kubernetes/ssl

#Generate etcd cert files

cfssl gencert -ca=/etc/kubernetes/ssl/ca.pem \
  -ca-key=/etc/kubernetes/ssl/ca-key.pem \
  -config=/etc/kubernetes/ssl/ca-config.json \
  -profile=kubernetes /etc/etcd/ssl/etcd-csr.json | cfssljson -bare etcd

mv -f etcd*.pem /etc/etcd/ssl
rm -f etcd.csr

#Generate k8s cert files

cfssl gencert -ca=/etc/kubernetes/ssl/ca.pem \
  -ca-key=/etc/kubernetes/ssl/ca-key.pem \
  -config=/etc/kubernetes/ssl/ca-config.json \
  -profile=kubernetes /etc/kubernetes/ssl/kubernetes-csr.json | cfssljson -bare kubernetes

mv -f kubernetes*.pem /etc/kubernetes/ssl/
rm -f kubernetes.csr

cfssl gencert -ca=/etc/kubernetes/ssl/ca.pem \
  -ca-key=/etc/kubernetes/ssl/ca-key.pem \
  -config=/etc/kubernetes/ssl/ca-config.json \
  -profile=kubernetes /etc/kubernetes/ssl/admin-csr.json | cfssljson -bare admin

mv -f admin*.pem /etc/kubernetes/ssl/
rm -f admin.csr

#Generate kube-proxy cert files

cfssl gencert -ca=/etc/kubernetes/ssl/ca.pem \
  -ca-key=/etc/kubernetes/ssl/ca-key.pem \
  -config=/etc/kubernetes/ssl/ca-config.json \
  -profile=kubernetes  /etc/kubernetes/ssl/kube-proxy-csr.json | cfssljson -bare kube-proxy

mv -f kube-proxy*.pem /etc/kubernetes/ssl/
rm -f kube-proxy.csr

