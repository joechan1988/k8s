#!/usr/bin/env bash

wget -c -O /usr/bin/cfssl https://pkg.cfssl.org/R1.2/cfssl_linux-amd64
wget -c -O /usr/bin/cfssljson https://pkg.cfssl.org/R1.2/cfssljson_linux-amd64
wget -c -O /usr/bin/cfssl-certinfo https://pkg.cfssl.org/R1.2/cfssl-certinfo_linux-amd64

chmod +x /usr/bin/cfssl
chmod +x /usr/bin/cfssljson
chmod +x /usr/bin/cfssl-certinfo