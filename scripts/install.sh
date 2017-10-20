#!/usr/bin/env bash

basepath=$(cd `dirname $0`; pwd)

yum install -y wget python2-pip.noarch bash-completion

pip install --upgrade pip
pip install -r ${basepath}/requirements.txt

${basepath}/deploy.py deploy

source /usr/share/bash-completion/bash_completion
source <(kubectl completion bash)
cat <<EOF >>/root/.bashrc
source <(kubectl completion bash)
EOF


