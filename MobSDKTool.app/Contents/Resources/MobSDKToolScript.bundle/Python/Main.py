#!/usr/bin/env python
import MobPods
from MobPods import *
prjPath = None
if  len(sys.argv) > 0:
    prjPath = sys.argv[0]
pods = MobPods ()
pods.run (prjPath)
