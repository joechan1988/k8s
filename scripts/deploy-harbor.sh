#!/usr/bin/env bash

#----Configurate ----



#----Check Config-----

echo "Current Node IP is :" $NODE_IP
echo "Master IP is :"$MASTER_IP
echo "Node Name is :"$NODE_NAME
echo "ETCD Nodes :" $ETCD_NODES
read -t 30 -p "Continue to Deploying or Reconfigure? [yN]" judge
if [[ $judge != 'y' ]]
then
  exit 0
fi

#------Create Certificate-----

echo "------Creating Certificate------"

cat > harbor-csr.json <<EOF
{
  "CN": "harbor",
  "hosts": [
    "127.0.0.1",
    "$NODE_IP",
    "$NODE_NAME"
  ],
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

cfssl gencert -ca=/etc/kubernetes/ssl/ca.pem \
  -ca-key=/etc/kubernetes/ssl/ca-key.pem \
  -config=/etc/kubernetes/ssl/ca-config.json \
  -profile=kubernetes harbor-csr.json | cfssljson -bare harbor

mkdir -p /etc/harbor/ssl
mv harbor*.pem /etc/harbor/ssl
rm -f harbor.csr  harbor-csr.json

#------Deploying----

echo "------Start Deploying------"

sed -i 's/{{hostname}}/'$NODE_IP'/g' ../harbor/harbor.cfg
docker load -i ../bin/harbor.tar.gz

source ../harbor/install.sh

