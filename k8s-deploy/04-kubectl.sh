#!/bin/bash

#Check binaries

if [ ! -f "/usr/bin/kubectl" ]
then
  echo "-------------"
  echo "No kubectl Binaries"
  echo "Download From \"https://dl.k8s.io/v1.6.2/kubernetes-server-linux-amd64.tar.gz \""
  exit 2
fi


#Check Env

if [[ ! -n "$MASTER_IP" || ! -n "$CLUSTER_KUBERNETES_SVC_IP" || ! -n "$KUBE_APISERVER" ]]
then
  echo "-------------"
  echo "Set env first"
  exit 2
fi

#Generate cert files

cat > admin-csr.json <<EOF
{
  "CN": "admin",
  "hosts": [],
  "key": {
    "algo": "rsa",
    "size": 2048
  },
  "names": [
    {
      "C": "CN",
      "ST": "BeiJing",
      "L": "BeiJing",
      "O": "system:masters",
      "OU": "System"
    }
  ]
}
EOF

cfssl gencert -ca=/etc/kubernetes/ssl/ca.pem \
  -ca-key=/etc/kubernetes/ssl/ca-key.pem \
  -config=/etc/kubernetes/ssl/ca-config.json \
  -profile=kubernetes admin-csr.json | cfssljson -bare admin

mv -f admin*.pem /etc/kubernetes/ssl/
rm admin.csr admin-csr.json

#Create kubeconfig file

kubectl config set-cluster kubernetes \
  --certificate-authority=/etc/kubernetes/ssl/ca.pem \
  --embed-certs=true \
  --server=${KUBE_APISERVER}

kubectl config set-credentials admin \
  --client-certificate=/etc/kubernetes/ssl/admin.pem \
  --embed-certs=true \
  --client-key=/etc/kubernetes/ssl/admin-key.pem

kubectl config set-context kubernetes \
  --cluster=kubernetes \
  --user=admin

kubectl config use-context kubernetes




