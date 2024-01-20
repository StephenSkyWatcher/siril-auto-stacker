import os
import shutil

def removeDir(d):
    if os.path.exists(d):
        shutil.rmtree(d)
    
def createDir(p):
    if not os.path.exists(p):
        os.makedirs(p)