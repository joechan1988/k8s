#!/usr/bin/env bash

curl -L -o /usr/bin/calicoctl -C - http://www.projectcalico.org/latest/calicoctl
chmod +x /usr/bin/calicoctl