#!/usr/bin/env bash

#pyinstaller -F ./kde/shell.py

if [ "$#" -eq 0 ];then
    docker build . -t kde:latest
else
    docker build . -t kde:$1
fi

#docker tag kde:1.7 joechan1988.asuscomm.com:10443/library/kde:1.7