#!/bin/bash

#Check binaries

if [[ ! -f "/usr/bin/kube-proxy" || ! -f "/usr/bin/kubelet" ]]
then
  echo "-------------"
  echo "No Binaries"
  echo "Download From \"https://dl.k8s.io/v1.6.2/kubernetes-server-linux-amd64.tar.gz \""
  exit 2
fi


#Check Env
#
#if [[ ! -n "$MASTER_IP" || ! -n "$BOOTSTRAP_TOKEN" || ! -n "$NODE_IP" || ! -n "$CLUSTER_DNS_SVC_IP" || ! -n "$CLUSTER_DNS_DOMAIN" || ! -n "$CLUSTER_KUBERNETES_SVC_IP" || ! -n "$KUBE_APISERVER" || ! -n "$SERVICE_CIDR" || ! -n "$NODE_PORT_RANGE" || ! -n "$ETCD_ENDPOINTS" ]]
#then
#  echo "-------------"
#  echo "Set env first"
#  exit 2
#fi


#kubelet

#--------copy kubeconfig from master---------

mkdir -p /etc/kubernetes/ssl
scp root@$MASTER_IP:/etc/kubernetes/bootstrap.kubeconfig /etc/kubernetes
scp root@$MASTER_IP:/etc/kubernetes/kubelet.kubeconfig /etc/kubernetes
scp root@$MASTER_IP:/etc/kubernetes/ssl/* /etc/kubernetes/ssl/

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


#-----------kube-config----------

scp root@$MASTER_IP:/etc/kubernetes/kube-proxy.kubeconfig /etc/kubernetes

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

#Approve csr

echo "------------------------------"
echo "You Need To Approve kubelet certification request by"
echo "\" kubectl get csr; \""
echo "\" kubectl certificate approve [csr_id_above]\""

#Label master node

kubectl label node $MASTER_IP node-role.kubernetes.io/master=""

