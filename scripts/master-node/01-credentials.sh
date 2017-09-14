#!/bin/bash

set -x

#Check Binaries

#if [ ! -f "/usr/bin/cfssl" ]
#then
#  wget https://pkg.cfssl.org/R1.2/cfssl_linux-amd64
#  chmod +x cfssl_linux-amd64
#  mv cfssl_linux-amd64 /usr/bin/cfssl
#fi
#
#if [ ! -f "/usr/bin/cfssljson" ]
#then
#  wget https://pkg.cfssl.org/R1.2/cfssljson_linux-amd64
#  chmod +x cfssljson_linux-amd64
#  mv cfssljson_linux-amd64 /usr/bin/cfssljson
#fi
#
#if [ ! -f "/usr/bin/cfssl-certinfo" ]
#then
#  wget https://pkg.cfssl.org/R1.2/cfssl-certinfo_linux-amd64
#  chmod +x cfssl-certinfo_linux-amd64
#  mv cfssl-certinfo_linux-amd64 /usr/bin/cfssl-certinfo
#fi

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



