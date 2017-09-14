#!/usr/bin/env bash

#----Configurate ----

source master-node/00-config.sh
source master-node/00-set-env.sh

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

#----Deploying----

echo "------Start Deploying------"
for i in {1..10}
do
source master-node/0$i-*.sh
done