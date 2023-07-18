#!/usr/bin/env python3

import subprocess
from multiprocessing import Pool
import os

def backup(src):
  dest = "data/prod_backup/"
  print("Backing up{} into {}".format(src, dest))
  subprocess.call(["rsync", "-arg", src, dest])
if __name__ == "__main__":
  src= "data/prod/"
  backup(src)

'''
  list_of_files = os.listdir(src)
  all_files = []
  for value in list_of_files:
    full_path = os.path.join(src, value)
    all_files.append(full_path)
'''

