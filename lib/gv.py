import os
import sys
sys.path.insert(0, os.getcwd())
import re
from lib.yorm import Yorm
import traceback as tb
cfg = {}
def getCfg():
    try:
        re1 = re.compile('\s*=\s*')
        lines = open(os.path.join(os.path.dirname(__file__), '../app.cfg')).readlines()
        incfg = False
        akey = None
        cfg = {}
        i = 0
        for line in lines:
            aline = line.strip()
            if aline[0] == '[' and aline[-1] == ']':
                incfg = True
                if len(aline) < 3:
                    raise Exception('Please give a config section name at line' + str(i) + 'of ../app.cfg')
                akey = aline[1: len(aline) - 1]
                cfg[akey] = {}
            sa = re1.split(aline)
            if len(sa) == 2:
                cfg[akey][sa[0].strip()] = sa[1].strip()
            elif len(sa) == 1:
                cfg[akey][sa[0].strip()] = ''
            i = i + 1
        return cfg
    except Exception as e:
        tb.print_tb(e.__traceback__)
        print(e)
        os._exit(-1)

def getDB(cfg):
    try:
        return Yorm(cfg)
    except Exception as e:
        tb.print_tb(e.__traceback__)
        print(e)
        os._exit(-1)
cfg = getCfg()
yorm = getDB(cfg['db'])
