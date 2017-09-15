#!/bin/bash

#set -x
#Check binaries

if [[ ! -f "/usr/bin/kubectl" || ! -f "/usr/bin/kube-apiserver" || ! -f "/usr/bin/kube-scheduler" || ! -f "/usr/bin/kube-controller-manager" || ! -f "/usr/bin/kube-proxy" || ! -f "/usr/bin/kubelet" ]]
then
  echo "-------------"
  echo "No kubectl Binaries"
  echo "Download From \"https://dl.k8s.io/v1.6.2/kubernetes-server-linux-amd64.tar.gz \""
  exit 2
fi


#Check Env

if [[ ! -n "$MASTER_IP" || ! -n "$CLUSTER_KUBERNETES_SVC_IP" || ! -n "$KUBE_APISERVER" || ! -n "$SERVICE_CIDR" || ! -n "$NODE_PORT_RANGE" || ! -n "$ETCD_ENDPOINTS" ]]
then
  echo "-------------"
  echo "Set env first"
  exit 2
fi

#Generate kubernetes cert files

cat > kubernetes-csr.json <<EOF
{
  "CN": "kubernetes",
  "hosts": [
    "127.0.0.1",
    "${MASTER_IP}",
    "${NODE_NAME}",
    "${CLUSTER_KUBERNETES_SVC_IP}",
    "kubernetes",
    "kubernetes.default",
    "kubernetes.default.svc",
    "kubernetes.default.svc.cluster",
    "kubernetes.default.svc.cluster.local"
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
  -profile=kubernetes kubernetes-csr.json | cfssljson -bare kubernetes

mkdir -p /etc/kubernetes/ssl/

mv -f kubernetes*.pem /etc/kubernetes/ssl/
rm -f kubernetes.csr  kubernetes-csr.json

cat > token.csv <<EOF
${BOOTSTRAP_TOKEN},kubelet-bootstrap,10001,"system:kubelet-bootstrap"
EOF
mv -f token.csv /etc/kubernetes/

#kube-apiserver


cat  > kube-apiserver.service <<EOF
[Unit]
Description=Kubernetes API Server
Documentation=https://github.com/GoogleCloudPlatform/kubernetes
After=network.target

[Service]
ExecStart=/usr/bin/kube-apiserver \\
  --admission-control=NamespaceLifecycle,LimitRanger,ServiceAccount,DefaultStorageClass,ResourceQuota \\
  --advertise-address=${MASTER_IP} \\
  --bind-address=${MASTER_IP} \\
  --insecure-bind-address=${MASTER_IP} \\
  --authorization-mode=RBAC \\
  --runtime-config=rbac.authorization.k8s.io/v1alpha1 \\
  --kubelet-https=true \\
  --experimental-bootstrap-token-auth \\
  --token-auth-file=/etc/kubernetes/token.csv \\
  --service-cluster-ip-range=${SERVICE_CIDR} \\
  --service-node-port-range=${NODE_PORT_RANGE} \\
  --tls-cert-file=/etc/kubernetes/ssl/kubernetes.pem \\
  --tls-private-key-file=/etc/kubernetes/ssl/kubernetes-key.pem \\
  --client-ca-file=/etc/kubernetes/ssl/ca.pem \\
  --service-account-key-file=/etc/kubernetes/ssl/ca-key.pem \\
  --etcd-cafile=/etc/kubernetes/ssl/ca.pem \\
  --etcd-certfile=/etc/kubernetes/ssl/kubernetes.pem \\
  --etcd-keyfile=/etc/kubernetes/ssl/kubernetes-key.pem \\
  --etcd-servers=${ETCD_ENDPOINTS} \\
  --enable-swagger-ui=true \\
  --allow-privileged=true \\
  --apiserver-count=3 \\
  --audit-log-maxage=30 \\
  --audit-log-maxbackup=3 \\
  --audit-log-maxsize=100 \\
  --audit-log-path=/var/lib/audit.log \\
  --event-ttl=1h \\
  --v=2
Restart=on-failure
RestartSec=5
Type=notify
LimitNOFILE=65536

[Install]
WantedBy=multi-user.target
EOF

mv -f  kube-apiserver.service /etc/systemd/system/

#kube-scheduler

cat > kube-scheduler.service <<EOF
[Unit]
Description=Kubernetes Scheduler
Documentation=https://github.com/GoogleCloudPlatform/kubernetes

[Service]
ExecStart=/usr/bin/kube-scheduler \\
  --address=127.0.0.1 \\
  --master=http://${MASTER_IP}:8080 \\
  --leader-elect=true \\
  --v=2
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

mv -f kube-scheduler.service /etc/systemd/system/

#kube-controller-manager

 cat > kube-controller-manager.service <<EOF
[Unit]
Description=Kubernetes Controller Manager
Documentation=https://github.com/GoogleCloudPlatform/kubernetes

[Service]
ExecStart=/usr/bin/kube-controller-manager \\
  --address=127.0.0.1 \\
  --master=http://${MASTER_IP}:8080 \\
  --allocate-node-cidrs=true \\
  --service-cluster-ip-range=${SERVICE_CIDR} \\
  --cluster-cidr=${CLUSTER_CIDR} \\
  --cluster-name=kubernetes \\
  --cluster-signing-cert-file=/etc/kubernetes/ssl/ca.pem \\
  --cluster-signing-key-file=/etc/kubernetes/ssl/ca-key.pem \\
  --service-account-private-key-file=/etc/kubernetes/ssl/ca-key.pem \\
  --root-ca-file=/etc/kubernetes/ssl/ca.pem \\
  --leader-elect=true \\
  --v=2
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

mv -f kube-controller-manager.service /etc/systemd/system/

#Start services

systemctl daemon-reload
systemctl enable kube-apiserver
systemctl enable kube-scheduler
systemctl enable kube-controller-manager

systemctl start kube-apiserver
systemctl start kube-scheduler
systemctl start kube-controller-manager



