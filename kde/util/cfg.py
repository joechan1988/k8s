#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import os

if sys.version_info[:3][0] == 2:
    import ConfigParser as ConfigParser
    import StringIO as StringIO

if sys.version_info[:3][0] == 3:
    import configparser as ConfigParser
    import io as StringIO


class conf(object):
    def __init__(self,cfgfile):
        # self.cfgfile=cfgfile
        conf = StringIO.StringIO()
        conf.write("[configuration]\n")
        conf.write(open(cfgfile).read())
        conf.seek(0, os.SEEK_SET)
        rcp = ConfigParser.RawConfigParser()
        rcp.readfp(conf)
        self.rcp = rcp

    def get_conf(self,conf_name):
        rcp =self.rcp
        conf_value = rcp.get('configuration',conf_name)
        return conf_value

    def load_all_config(self):
        # master_ip = rcp.get("configuration", "master_ip")
        # kube_apiserver = "https://" + node_ip + ":6443"
        rcp = self.rcp
        for key, value in rcp.items("configuration"):
            self.__setattr__(key, value)
        # print self.update_binaries

    def test(self):
        rcp = self.rcp
        print(rcp.items("configuration"))
        for key,value in rcp.items("configuration"):
            self.__setattr__(key,value)
        print self.update_binaries