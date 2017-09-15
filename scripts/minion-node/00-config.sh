#!/bin/bash
# SET ENV
#set -x

#------Custom Config------
export NODE_IP="172.31.0.119"
export MASTER_IP="172.31.0.119"
export BOOTSTRAP_TOKEN="41f7e4ba8b7be874fcff18bf5cf41a7c"
export SERVICE_CIDR="10.254.0.0/16"
export CLUSTER_CIDR="172.30.0.0/16"
export NODE_PORT_RANGE="8400-9000"
export CLUSTER_KUBERNETES_SVC_IP="10.254.0.1"
export CLUSTER_DNS_SVC_IP="10.254.0.2"
export CLUSTER_DNS_DOMAIN="cluster.local."


