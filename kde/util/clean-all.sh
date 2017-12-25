#!/usr/bin/env bash

systemctl stop etcd kube-apiserver kubelet kube-proxy kube-controller-manager kube-scheduler docker
rm -rf /var/lib/etcd/
umount /var/lib/kubelet/pods/*/volumes/*/*
rm -rf /var/lib/kubelet/
rm -rf /etc/kubernetes/