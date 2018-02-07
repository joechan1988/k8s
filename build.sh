#!/usr/bin/env bash

#pyinstaller -F ./kde/shell.py
docker build . -t kde:1.7

docker tag kde:1.7 joechan1988.asuscomm.com:10443/library/kde:1.7