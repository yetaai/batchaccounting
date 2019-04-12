from lib.gv import cfg, yorm
import re
import traceback as tb
import os
import sys
sys.path.insert(0, os.getcwd())

def createTables():
    yorm.db.query('create database if not exists ' + cfg['db']['db'] + ' character set utf8mb4')
    re1 = re.compile(';')
    sqls = re1.split(open(os.path.join(os.path.dirname(__file__), 'initdb.sql')).read())
    for sql in sqls:
        if len(sql.strip()) > 10:
            yorm.db.query(sql)
    yorm.db.query('commit')
def dropTables():
    if yorm.tbldefs is None:
        return
    if len(yorm.tbldefs) == 0:
        return
    for tn, tbldef in yorm.tbldefs.items():
        try:
            yorm.db.query('drop table if exists ' + tn)
        except Exception as e:
            tb.print_tb(e.__traceback__)
            print(e)
            os._exit(-1)
    yorm.db.query('commit')
def loadCfgRecs():
    c = yorm.db.cursor()
    c.execute('select max(orga) as orga from orga')
    r = c.fetchall()
    if r is None or len(r) == 0 or r[0] is None or r[0][0] is None:
        maxOrg = 0
    else:
        maxOrg = r[0][0] + 1
    orgas = []
    for cfgKey, aCfg in cfg.items():
        if cfgKey[:4].lower() == 'org-':
            anOrga = {'orga': maxOrg, 'sname': aCfg['sname'],
                      'url': aCfg['url'], 'usr': aCfg['usr'],
                      'password': aCfg['password'], 'earliest': aCfg['earliest'],
                      'txt': aCfg['txt'], 'usrxpath': aCfg['usrxpath'],
                      'passxpath': aCfg['passxpath'], 'loginxpath': aCfg['loginxpath']}
            dbOrga = yorm.getmany('orga', ' where sname = "' + aCfg['sname'] + '"')
            if dbOrga is None or len(dbOrga) == 0:
                maxOrg = maxOrg + 1
            else:
                anOrga['orga'] = dbOrga[0]['orga']
            orgas.append(anOrga)
    try:
        yorm.savemany('orga', orgas, insertOrUpdate=False)
        yorm.db.query('commit')
    except Exception as e:
        tb.print_tb(e.__traceback__)
        print(e)
        yorm.db.query('rollback')
if __name__ == '__main__':
    loadCfgRecs()