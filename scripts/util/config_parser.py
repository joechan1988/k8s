
import os
import yaml

class Config(object):
    def __init__(self,config_path):
        self.config_path = config_path

    def load(self):

        config_file = file(self.config_path,'r')
        configs = yaml.load(config_file)
        self.data = configs

