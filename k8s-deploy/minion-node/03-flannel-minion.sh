#!/bin/bash

#Check binaries

if [[ ! -f "/usr/bin/dockerd-current" || ! -f "/usr/bin/flanneld" ]]
then
  echo "-------------"
  echo "No Docker or flanneld binaries"
  echo "Download flannel from \"https://github.com/coreos/flannel/releases \""
  exit 2
fi


#Check Env

if [[ ! -n "${ETCD_ENDPOINTS}" || ! -n "${FLANNEL_ETCD_PREFIX}" || ! -n "${CLUSTER_CIDR}" ]]
then
  echo "-------------"
  echo "Set env first : ETCD_ENDPOINTS ,FLANNEL_ETCD_PREFIX , CLUSTER_CIDR"
  exit 2
fi



# configure docker.service

cat > docker.service <<EOF
[Unit]
Description=Docker Application Container Engine
Documentation=http://docs.docker.com
After=network.target
Wants=docker-storage-setup.service

[Service]
Type=notify
NotifyAccess=all
EnvironmentFile=-/etc/sysconfig/docker
EnvironmentFile=-/etc/sysconfig/docker-storage
EnvironmentFile=-/etc/sysconfig/docker-network
EnvironmentFile=-/run/flannel/docker
Environment=GOTRACEBACK=crash
Environment=DOCKER_HTTP_HOST_COMPAT=1
Environment=PATH=/usr/libexec/docker:/usr/bin:/usr/sbin
ExecStart=/usr/bin/dockerd-current \
          --add-runtime docker-runc=/usr/libexec/docker/docker-runc-current \
          --default-runtime=docker-runc \
          --exec-opt native.cgroupdriver=systemd \
          --userland-proxy-path=/usr/libexec/docker/docker-proxy-current \
          \$OPTIONS \
          \$DOCKER_STORAGE_OPTIONS \
          \$DOCKER_NETWORK_OPTIONS \
          \$ADD_REGISTRY \
          \$BLOCK_REGISTRY \
          \$INSECURE_REGISTRY
ExecReload=/bin/kill -s HUP \$MAINPID
LimitNOFILE=1048576
LimitNPROC=1048576
LimitCORE=infinity
TimeoutStartSec=0
Restart=on-abnormal

[Install]
WantedBy=multi-user.target
EOF

iptables -P FORWARD ACCEPT

mv docker.service /etc/systemd/system

# configure flanneld.service

cat > flanneld.service << EOF
[Unit]
Description=Flanneld overlay address etcd agent
After=network.target
After=network-online.target
Wants=network-online.target
After=etcd.service
Before=docker.service

[Service]
Type=notify
ExecStart=/usr/bin/flanneld \\
  -etcd-cafile=/etc/kubernetes/ssl/ca.pem \\
  -etcd-certfile=/etc/flanneld/ssl/flanneld.pem \\
  -etcd-keyfile=/etc/flanneld/ssl/flanneld-key.pem \\
  -etcd-endpoints=${ETCD_ENDPOINTS} \\
  -etcd-prefix=${FLANNEL_ETCD_PREFIX}
ExecStartPost=/usr/bin/mk-docker-opts.sh -k DOCKER_NETWORK_OPTIONS -d /run/flannel/docker
Restart=on-failure

[Install]
WantedBy=multi-user.target
RequiredBy=docker.service
EOF

mv -f flanneld.service /etc/systemd/system/

# Copy flannel cert files from master (Minion node)

mkdir -p /etc/flanneld/ssl
scp root@$MASTER_IP:/etc/flanneld/ssl/* /etc/flanneld/ssl/


#Start docker & flanneld service

systemctl daemon-reload
systemctl enable flanneld
systemctl enable docker
systemctl start flanneld

systemctl restart docker

# check state

service_running=$(journalctl  -u flanneld |grep 'Lease acquired')
nic_running=$(ifconfig flannel.1)

if [[ -n "$service_running" && -n "$nic_running" ]]
then
   echo "flanneld is running"
fi

