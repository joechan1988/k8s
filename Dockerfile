FROM ubuntu:16.04

RUN apt-get update && \
        apt-get install --no-install-recommends -y \
        arptables \
        bridge-utils \
        ca-certificates \
        conntrack \
        curl \
        wget \
        ethtool \
        iproute2 \
        iptables \
        iputils-ping \
        jq \
        kmod \
        openssl \
        psmisc \
        python2.7 \
        tcpdump \
        vim-tiny \
        python-pip \
        python-dev \
        python-setuptools \
        build-essential

RUN apt-get install --no-install-recommends -y git python-yaml && \
    pip install --upgrade pip

COPY ./kde /kde/kde
COPY ./addons /kde/addons
COPY ./bin /kde/bin
COPY ./.git /kde/.git
COPY ["./setup.py","./setup.cfg","./requirements.txt","ChangeLog","AUTHORS","/kde/"]
WORKDIR /kde/

RUN mkdir -p /tmp/bin && \
    cp -f bin/kubectl /usr/bin && \
    mv -f bin/cfssl* /usr/bin && \
    mv -f bin/kube* /tmp/bin && \
    mv -f bin/etcd* /tmp/bin && \
    mv -f bin/docker* /usr/bin && \
    chmod +x /usr/bin/cfssl* \
              /usr/bin/kubectl \
              /usr/bin/docker \
              /usr/bin/docker-compose

RUN pip install -U .