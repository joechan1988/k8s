#!/usr/bin/python

"""
Attention: Run this after docker image build
"""

import os, sys,shutil
import subprocess

current_path = os.getcwd()

dist_path = os.path.join(current_path, "dist")
doc_path = os.path.join(current_path,"doc")

if os.path.exists(doc_path):
    shutil.rmtree(doc_path)

os.makedirs(doc_path)

print("---Copying tar files---")
shutil.copytree(doc_path,os.path.join(dist_path,"doc"))

print("---Generating dist package---")
ps = subprocess.Popen("tar -cvf kde-dist.tar dist/",shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)

while ps.poll() is None:
    line = ps.stdout.readline()
    line = line.strip()
    if line:
        print(line)

if ps.returncode == 0:
    print("Finished")
else:
    print("Failed")






