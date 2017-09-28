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

mkdir -p /etc/etcd/ssl

cfssl gencert -ca=/etc/kubernetes/ssl/ca.pem \
  -ca-key=/etc/kubernetes/ssl/ca-key.pem \
  -config=/etc/kubernetes/ssl/ca-config.json \
  -profile=kubernetes /etc/etcd/ssl/etcd-csr.json | cfssljson -bare etcd

mv -f etcd*.pem /etc/etcd/ssl
rm -f etcd.csr



