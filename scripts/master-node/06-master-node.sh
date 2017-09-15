#!/bin/bash

#set -x
#Check binaries

if [[ ! -f "/usr/bin/kube-proxy" || ! -f "/usr/bin/kubelet" ]]
then
  echo "-------------"
  echo "No Binaries"
  echo "Download From \"https://dl.k8s.io/v1.6.2/kubernetes-server-linux-amd64.tar.gz \""
  exit 2
fi


#Check Env

if [[ ! -n "$MASTER_IP" || ! -n "$BOOTSTRAP_TOKEN" || ! -n "$NODE_IP" || ! -n "$CLUSTER_DNS_SVC_IP" || ! -n "$CLUSTER_DNS_DOMAIN" || ! -n "$CLUSTER_KUBERNETES_SVC_IP" || ! -n "$KUBE_APISERVER" || ! -n "$SERVICE_CIDR" || ! -n "$NODE_PORT_RANGE" || ! -n "$ETCD_ENDPOINTS" ]]
then
  echo "-------------"
  echo "Set env first"
  exit 2
fi


#kubelet

#--------kubeconfig---------

kubectl create clusterrolebinding kubelet-bootstrap --clusterrole=system:node-bootstrapper --user=kubelet-bootstrap

kubectl config set-cluster kubernetes \
  --certificate-authority=/etc/kubernetes/ssl/ca.pem \
  --embed-certs=true \
  --server=${KUBE_APISERVER} \
  --kubeconfig=bootstrap.kubeconfig

kubectl config set-credentials kubelet-bootstrap \
  --token=${BOOTSTRAP_TOKEN} \
  --kubeconfig=bootstrap.kubeconfig

kubectl config set-context default \
  --cluster=kubernetes \
  --user=kubelet-bootstrap \
  --kubeconfig=bootstrap.kubeconfig

kubectl config use-context default --kubeconfig=bootstrap.kubeconfig

mv -f bootstrap.kubeconfig /etc/kubernetes/

#--------systemd unit files--------

mkdir /var/lib/kubelet

cat > kubelet.service <<EOF
[Unit]
Description=Kubernetes Kubelet
Documentation=https://github.com/GoogleCloudPlatform/kubernetes
After=docker.service
Requires=docker.service

[Service]
WorkingDirectory=/var/lib/kubelet
ExecStart=/usr/bin/kubelet \\
  --address=${NODE_IP} \\
  --hostname-override=${NODE_IP} \\
  --pod-infra-container-image=registry.access.redhat.com/rhel7/pod-infrastructure:latest \\
  --experimental-bootstrap-kubeconfig=/etc/kubernetes/bootstrap.kubeconfig \\
  --kubeconfig=/etc/kubernetes/kubelet.kubeconfig \\
  --require-kubeconfig \\
  --cert-dir=/etc/kubernetes/ssl \\
  --cluster_dns=${CLUSTER_DNS_SVC_IP} \\
  --cluster_domain=${CLUSTER_DNS_DOMAIN} \\
  --hairpin-mode promiscuous-bridge \\
  --allow-privileged=true \\
  --serialize-image-pulls=false \\
  --logtostderr=true \\
  --cgroup-driver=systemd \\
  --v=2

ExecStopPost=/sbin/iptables -A INPUT -s 10.0.0.0/8 -p tcp --dport 4194 -j ACCEPT
ExecStopPost=/sbin/iptables -A INPUT -s 172.16.0.0/12 -p tcp --dport 4194 -j ACCEPT
ExecStopPost=/sbin/iptables -A INPUT -s 192.168.0.0/16 -p tcp --dport 4194 -j ACCEPT
ExecStopPost=/sbin/iptables -A INPUT -p tcp --dport 4194 -j DROP
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF


mv -f kubelet.service /etc/systemd/system/kubelet.service


#kube-proxy

#----------cert files----------

cat > kube-proxy-csr.json <<EOF
{
  "CN": "system:kube-proxy",
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
      "O": "k8s",
      "OU": "System"
    }
  ]
}
EOF

cfssl gencert -ca=/etc/kubernetes/ssl/ca.pem \
  -ca-key=/etc/kubernetes/ssl/ca-key.pem \
  -config=/etc/kubernetes/ssl/ca-config.json \
  -profile=kubernetes  kube-proxy-csr.json | cfssljson -bare kube-proxy

mv -f kube-proxy*.pem /etc/kubernetes/ssl/
rm -f kube-proxy.csr  kube-proxy-csr.json

#-----------kube-config----------

kubectl config set-cluster kubernetes \
  --certificate-authority=/etc/kubernetes/ssl/ca.pem \
  --embed-certs=true \
  --server=${KUBE_APISERVER} \
  --kubeconfig=kube-proxy.kubeconfig

kubectl config set-credentials kube-proxy \
  --client-certificate=/etc/kubernetes/ssl/kube-proxy.pem \
  --client-key=/etc/kubernetes/ssl/kube-proxy-key.pem \
  --embed-certs=true \
  --kubeconfig=kube-proxy.kubeconfig

kubectl config set-context default \
  --cluster=kubernetes \
  --user=kube-proxy \
  --kubeconfig=kube-proxy.kubeconfig

kubectl config use-context default --kubeconfig=kube-proxy.kubeconfig

mv -f kube-proxy.kubeconfig /etc/kubernetes/

#-----------systemd unit files-----------

mkdir -p /var/lib/kube-proxy

cat > kube-proxy.service <<EOF
[Unit]
Description=Kubernetes Kube-Proxy Server
Documentation=https://github.com/GoogleCloudPlatform/kubernetes
After=network.target

[Service]
WorkingDirectory=/var/lib/kube-proxy
ExecStart=/usr/bin/kube-proxy \\
  --bind-address=${NODE_IP} \\
  --hostname-override=${NODE_IP} \\
  --cluster-cidr=${SERVICE_CIDR} \\
  --kubeconfig=/etc/kubernetes/kube-proxy.kubeconfig \\
  --logtostderr=true \\
  --v=2
Restart=on-failure
RestartSec=5
LimitNOFILE=65536

[Install]
WantedBy=multi-user.target
EOF

mv -f kube-proxy.service /etc/systemd/system/

#Start services

systemctl daemon-reload
systemctl enable kube-proxy
systemctl enable kubelet
systemctl start kubelet
systemctl start kube-proxy

#Creating CSR auto approving

echo "---Creating CSR auto approving---"

kubectl apply -f ../addons/csr-auto-approve.yml

#Approve csr

echo "------------------------------"
echo "You Need To Approve kubelet certification request by"
echo "\" kubectl get csr; \""
echo "\" kubectl certificate approve [csr_id_above]\""

#Label master node

kubectl label node $MASTER_IP node-role.kubernetes.io/master=""
kubectl label node $MASTER_IP kubeadm.alpha.kubernetes.io/role=master

