#!/usr/bin/env bash

kubectl -n kube-system create secret generic calico-etcd-secrets --from-file=etcd-ca=/etc/kubernetes/ssl/ca.pem \
--from-file=etcd-cert=/etc/kubernetes/ssl/kubernetes.pem \
--from-file=etcd-key=/etc/kubernetes/ssl/kubernetes-key.pem