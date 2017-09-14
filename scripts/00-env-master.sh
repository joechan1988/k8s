# SET ENV

export NODE_IP="192.168.1.184"
export NODE_NAME=$NODE_IP
export HOSTNAME=$NODE_NAME
sysctl kernel.hostname=$NODE_NAME
cat > /etc/hostname << EOF
echo $NODE_IP
EOF

export MASTER_IP="192.168.1.184"
export BOOTSTRAP_TOKEN="41f7e4ba8b7be874fcff18bf5cf41a7c"
export KUBE_APISERVER="https://${MASTER_IP}:6443"

export SERVICE_CIDR="10.254.0.0/16"
export CLUSTER_CIDR="172.30.0.0/16"
export NODE_PORT_RANGE="8400-9000"

export ETCD_ENDPOINTS="https://${MASTER_IP}:2379"
export FLANNEL_ETCD_PREFIX="/kubernetes/network"
export ETCD_NODES=${NODE_NAME}=https://${MASTER_IP}:2380

export CLUSTER_KUBERNETES_SVC_IP="10.254.0.1"
export CLUSTER_DNS_SVC_IP="10.254.0.2"
export CLUSTER_DNS_DOMAIN="cluster.local."

mkdir /etc/kubernetes

