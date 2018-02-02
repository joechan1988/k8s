#!/usr/bin/env bash

docker run \
        -t -i --net=host --rm \
        -v /var/run/docker.sock:/var/run/docker.sock:ro \
        -v /etc/kde:/etc/kde \
        -v /etc/localtime:/etc/localtime:ro \
        kde:0.1 \
        kde \
        deploy

docker load -i /etc/kde/addons/images/*

kubectl --kubeconfig=/etc/kde/auth/admin.kubeconfig apply -f /etc/kde/addons/DNS/