import os
from lib.gv import cfg, yorm
import copy
from lib.appdb import createTables, dropTables, loadCfgRecs
import traceback as tb
import re
from lib.webquote import makeChromeDriver
import time
import datetime
import sys
from ofxtools.Parser import OFXTree

from selenium import webdriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.common.exceptions import TimeoutException

track = []
def initTrack():
    tracks = yorm.getmany('track', ' order by trackid desc limit 0, 1')
    if tracks is None or len(tracks) == 0:
        atrack = {'trackid': 0, 'txt': 'First by sys', 'isdefault': True}
        yorm.saveone('track', atrack)
        yorm.db.query('commit')
        track.append(atrack)
    else:
        track.extend(tracks)

def changeTrack():
    s0 = 'Choose track to change: \n'
    tracks = yorm.getmany('track', ' order by trackid desc')
    re1 = re.compile('\s+')
    for i in len(tracks):
        atrack = tracks[i]
        s0 = s0 + str(i) + ': ' + atrack + '\n'
    while 1:
        s = input(s0)
        if s == 'q':
            return
        try:
            sa = re1.split(s)
            if len(sa) != 2 and len(sa) != 1:
                print('Input n xxx. n is track, xxx is description')
                continue
            if len(sa) == 2:
                newTrack = {}
                newTrack['trackid'] = int(sa[0])
                newTrack['txt'] = sa[1]
                newTrack['isdefault'] = True
                yorm.saveone('track', newTrack)
                print('New track created and set to default')
            else:
                i = int(sa[0])
                if i < 0 or i >= len(tracks):
                    print('Input n to switch to default. n xxx to create new Track')
                    continue
                for atrack in tracks:
                    if atrack['isdefault']:
                        atrack['isdefault'] = False
                        yorm.saveone('track', atrack)
                        break
                tracks[i]['isdefault'] = True
                yorm.saveone('trackid', tracks[i])
                print('Track changed to', i)
            yorm.db.query('commit')
            return
        except Exception as e:
            yorm.db.query('rollback')
            tb.print_tb(e.__traceback__)
            print(e)
            os._exit(-1)
def showAccounts():
    orgas = yorm.getmany('orga', 'order by orga')
    accounts = yorm.getmany('acc', ' order by orga, acc')

    i0 = -1
    i1 = 0
    anOrga = None
    lastAcc = None
    while i1 < len(accounts):
        anAccount = accounts[i1]
        if lastAcc is None or lastAcc['orga'] != anAccount['orga']:
            while i0 < len(orgas):
                i0 = i0 + 1
                anOrga = orgas[i0]
                if anOrga['orga'] == anAccount['orga']:
                    break
        s = '==' + str(anOrga['orga']) + '-' + str(anAccount['acc']) + ', organization name: ' + anOrga['sname'] + ', acckey: ' + anAccount['accno'] + ', acctype: ' + anAccount['acctype'] + ', routine no: ' + anAccount['routineno'] + ', most days to download: ' + str(anAccount['dayspan']) + ', text: ' + anAccount['txt'] + '\n'
        print(s)
        lastAcc = anAccount
        i1 = i1 + 1
def impOrga(anOrga, ptrack=None, driver=None):
    wd = driver if driver is not None else makeChromeDriver(headless=False)
    wd.maximize_window()
    try:
        wd.get(anOrga['url'])
        # bodyhtml = driver.find_elements(By.TAG_NAME, 'body')[0].get_attribute('innerHTML').lower()
        login(wd, anOrga)
        findAndDownloadOrga(wd, anOrga, ptrack)
        impFile()
    except Exception as e:
        tb.print_tb(e.__traceback__)
        print(e)
        pass
    finally:
        if driver is None:
            wd.close()
def impAccount(sacc):
    if sacc is None:
        impAllAcc()
        return
    re2 = re.compile('\-')
    try:
        saAcc = re2.split(sacc)
        anOrga = yorm.getone('orga', {'orga': saAcc[0]})
        anAcc = yorm.getone('acc', {'orga': int(saAcc[0]), 'acc': int(saAcc[1])})
        impOne(anOrga, anAcc)
    except Exception as e:
        tb.print_tb(e.__traceback__)
        print(e)
def expAccount(sacc):
    if sacc is None:
        expAllAcc()
        return
    re2 = re.compile('\-')
    try:
        saAcc = re2.split(sacc)
        anOrga = yorm.getone('orga', {'orga': saAcc[0]})
        anAcc = yorm.getone('acc', {'orga': int(saAcc[0]), 'acc': int(saAcc[1])})
        expOne(anOrga, anAcc)
    except Exception as e:
        tb.print_tb(e.__traceback__)
        print(e)
def impAllAcc():
    orgas = yorm.getmany('orga', '')
    wd = makeChromeDriver()
    for anOrga in orgas:
        accs = yorm.getmany('acc', ' where orga = ' + anOrga['orga'])
        for anAcc in accs:
            impOne(anOrga, anAcc, ptrack=track[0],driver=wd)
    wd.close()
def expAllAcc():
    orgas = yorm.getmany('orga')
    wd = makeChromeDriver()
    for anOrga in orgas:
        accs = yorm.getmany('acc', ' where orga = ' + anOrga['orga'])
        for anAcc in accs:
            expOne(anOrga, anAcc)
    wd.close()
def impOne(anOrga, anAcc, ptrack=None, driver:webdriver=None):
    wd = driver if driver is not None else makeChromeDriver()
    try:
        wd.get(anOrga['url'])
        bodyhtml = driver.find_elements(By.TAG_NAME, 'body')[0].get_attribute('innerHTML').lower()
        login(wd, anOrga, anAcc, bodyhtml)
        findAndDownload(wd, anOrga, anAcc, ptrack, bodyhtml)
        impFile()
    except:
        pass
    finally:
        if driver is None:
            wd.close()
def impFile():
    a = None
def login(driver:webdriver, orga):
    try:
        usernameMask = None
        username = None
        re1 = re.compile('/')
        sausername = re1.split(orga['usrxpath'])
        while 1:
            try:
                usernameMask = WebDriverWait(driver, 1).until(EC.presence_of_element_located((By.ID, sausername[0])))
                break
            except Exception as e:
                pass
        # username = driver.find_element_by_id(orga['usrxpath'])
        usernameMask.click()
        time.sleep(0.1)
        username = driver.find_element_by_id(sausername[1])
        username.click()
        time.sleep(0.1)
        username.click()
        time.sleep(0.1)

        username.send_keys(orga['usr'])
        password = driver.find_element_by_id(orga['passxpath'])
        password.send_keys(orga['password'])
        password.send_keys(Keys.ENTER)
    except Exception as e:
        raise e
def findAndDownloadOrga(wd, orga, ptrack):
    if orga['url'].lower().find('citi') >= 0:
        citidownload(wd, orga, ptrack)
    elif orga['url'].lower().find('wellsfargo') > 0:
        wfdownload()
    else:
        print('Unknown institution: ', orga)
def findAndDownload(wd, orga, acc, ptrack):
    if orga['url'].lower().find('citi') >= 0:
        citidownload(wd, orga, ptrack)
    else:
        wfdownload()
def citidownload(wd:webdriver, orga, ptrack, pacc=None):
    accountNamesWords = ['interest checking', 'savings plaus' ]
    re1 = re.compile('\s*\-\s*')
    try:
        print('-----------citidownload')
        wd.implicitly_wait(10)
        # WebDriverWait(wd, 10).until(EC.presence_of_element_located((By.XPATH, '')))
        webArchs = wd.find_elements(By.TAG_NAME, 'a')
        print('-----------citidownload, 1')
        for arch in webArchs:
            print('-----------citidownload, 2')
            stext = arch.get_attributes('text')
            print('-----------citidownload, 3, ', stext)
            satext = re1.split(stext.strip())
            if len(satext) != 2:
                continue
            if satext[0] not in accountNamesWords:
                continue
            if len(satext[1]) != 4:
                continue
            try:
                last4digis = int(satext[0])
            except Exception as e:
                continue
            href = arch.get_attributes('href')
            if href.find('JFP_TOKEN') <= 10:
                continue
            arch.click()
            dropDowns = wd.find_elements((By.XPATH, '//div[@class="dropdown"]/svg'))
            for dropDown in dropDowns:
                lastDaysWe = dropDown.find_element((By.XPATH, 'preceding-sibling::::div'))
                lastDays = lastDays.get_attributes('text')
                if lastDays[-4:] == 'days' or lastDays[-6:] == 'months' or lastDays == 'specific date' or lastDays == 'customdaterange':
                    if lastDays != 'custom date range':
                        dropDown.click()
                        break
            startDateEle = None
            endDateEle = None
            downloadEle = None
            downloadEle.click()
            QFXEles = wd.find_elements((By.XPATH, '//input[@type="radio"]'))
            for aQFX in QFXEles:
                aQFXText = aQFX.get_attributes('text')
                if aQFXText[:3] == 'QFX':
                    btns = wd.find_elements((By.XPATH, '//button[@type="button"]'))
                    for btn in btns:
                        btnTxt = btn.get_attributes('text')
                        if btnTxt.lower() == 'download':
                            btnTxt.click()
                            closeEle = wd.find_elements((By.XPATH, '//'))
                            closeEle.click()
                            break
            #loop Download directory and find the newest one and move to data directory
    except Exception as e:
        tb.print_tb(e.__traceback__)
        print(e)
def wfdownload():
    a = None
def expOne(anOrga, anAcc, ptrack=None):
    path = cfg['datadir']['dir']
def mainloop():
    initTrack()
    s0 = 'Choose command to go\n' \
         ' 1: drop tables and clean data\n' \
         ' 2: create tables and load\n' \
         ' 3: show track id(used for export only)\n' \
         ' 4: show accounts\n' \
         ' 5: import for account \n' \
         ' 6: export for account \n' \
         ' 7: one step all accounts import / export\n'
    while 1:
        s = input(s0)
        if s == '1':
            dropTables()
            os.system('rm -rf ' + os.path.join(os.path.dirname(__file__), cfg['datadir']['dir']))
        elif s == '2':
            createTables()
            loadCfgRecs()
        elif s == '3':
            print('Tracking: ', track[0])
            changeTrack()
        elif s[0] == '4':
            showAccounts(s[1:])
        elif s[0] == '5':
            orgas = yorm.getmany('orga', '')
            for orga in orgas:
                print(orga)
                impOrga(orga, ptrack=track[0])
                break
        elif s[0] == '6':
            expAccount(s[1:])
        elif s == '7':
            impAllAcc()
            expAccount()
import codecs
def localImp(tranloader):
    try:
        datadir = cfg['datadir']['dir']
        if datadir is None or len(datadir) == 0:
            raise Exception('Config dir in datadir section is not found')
        if datadir[0] == '/':
            absDataDir = datadir
        else:
            absDataDir = os.path.join(os.path.dirname(__file__), datadir)
        rawFiles = os.listdir(absDataDir)
        i = 0
        for rawfile in rawFiles:
            if len(rawfile) <= 3 or (len(rawfile) > 3 and rawfile[-3:].lower() not in ['qfx', 'ofx']):
                continue
            i = i + 1
        if i == 0:
            print('No data file is found')
        for rawfile in rawFiles:
            if len(rawfile) <= 3 or (len(rawfile) > 3 and rawfile[-3:].lower() not in ['qfx', 'ofx']):
                continue
            postfix = rawfile[-4:].lower()
            rawPath = os.path.join(absDataDir, rawfile)
            print('Processing', rawPath)
            if postfix in ['.qfx', '.ofx']:
                impid = ofxParse(rawPath, tranloader)
                moveToLoaded(rawPath, rawfile, impid)
            else:
                print('File type not supported: ' + postfix)
                continue
    except Exception as e:
        tb.print_tb(e.__traceback__)
        print(e)
def moveBack():
    try:
        datadir = cfg['datadir']['dir']
        if datadir is None or len(datadir) == 0:
            raise Exception('Config dir in datadir section is not found')
        if datadir[0] == '/':
            absDataDir = datadir
        else:
            absDataDir = os.path.join(os.path.dirname(__file__), datadir)
        loadedDir = os.path.join(absDataDir, 'loaded')
        for afile in os.listdir(loadedDir):
            i = afile.find('_')
            oriFn = os.path.join(absDataDir, afile[i + 1:])
            impFn = os.path.join(loadedDir, afile)
            os.rename(impFn, oriFn)
    except Exception as e:
        tb.print_tb(e.__traceback__)
        print(e)
        os._exit(-1)


def moveToLoaded(rawPath, rawfile, impid):
    try:
        datadir = cfg['datadir']['dir']
        if datadir is None or len(datadir) == 0:
            raise Exception('Config dir in datadir section is not found')
        if datadir[0] == '/':
            absDataDir = datadir
        else:
            absDataDir = os.path.join(os.path.dirname(__file__), datadir)
        loadedDir = os.path.join(absDataDir, 'loaded')
        if not os.path.exists(loadedDir):
            os.mkdir(loadedDir)
        newFile = 'imp' + str(impid) + '_' + rawfile
        os.rename(rawPath, os.path.join(loadedDir, newFile))
    except Exception as e:
        tb.print_tb(e.__traceback__)
        print(e)
        os._exit(-1)
def ofxParse(file, tranloader):
    parser = OFXTree()
    with codecs.open(file, 'br') as fileobj:
        parser.parse(fileobj)
    ofx = parser.convert()
    sonr = ofx.sonrs
    statement = ofx.statements[0]
    acc = ofx.statements[0].account

    orga = getOrga(sonr, acc)
    impid = round(datetime.datetime.now().timestamp())
    for statement in ofx.statements:
        acc = getAcc(orga, statement)
        for tran in statement.transactions:
            tranloader.add(tran, orga, acc)
        tranloader.post(statement, impid)
    return impid
    # for transaction in ofx.account.statement.transactions:
    #     print('payee', transaction.payee)
    #     print('type', transaction.type)
    #     print('date', transaction.date)
    #     print('amount', transaction.amount)
    #     print('id', transaction.id)
    #     print('memo', transaction.memo)
    #     print('sic', transaction.sic)
    #     print('mcc', transaction.mcc)
    #     print('checksum', transaction.checknum)
def getAcc(orga, statement):
    try:
        stmtAcc = statement.account
        stmtLast4 = stmtAcc.acctid[-4:]
        accs = yorm.getmany('acc', ' where orga = ' + str(orga['orga']))
        if accs is not None and len(accs) > 0:
            for acc in accs:
                last4 = acc['accno'][-4:]
                if last4 == stmtLast4:
                    syncdate = round(statement.ledgerbal.dtasof.timestamp())
                    if syncdate > acc['syncdate']:
                        acc['syncbal'] = round(statement.ledgerbal.balamt, 2)
                        acc['syncdate'] = syncdate
                        try:
                            yorm.saveone('acc', acc, insertOrReqplace=False)
                            yorm.db.query('commit')
                        except Exception as e:
                            yorm.db.query('rollback')
                            tb.print_tb(e.__traceback__)
                            print(e)
                            os._exit(-1)
                    return acc
        sinput = input('Account ' + stmtLast4 + ' is not found. Create automatically or select one?\n'
                                                '    y: Create\n'
                                                '    s: Select\n'
                                                'other: quit\n')
        if sinput == 'y':
            c = yorm.db.cursor()
            c.execute('select max(acc) as acc from acc where orga = ' + str(orga['orga']))
            r = c.fetchall()
            if r is None or len(r) == 0 or r[0] is None or r[0][0] is None:
                maxAcc = 0
            else:
                maxAcc = r[0][0] + 1
            syncdate = round(statement.ledgerbal.dtasof.timestamp())
            anAcc = {'orga': orga['orga'], 'acc': maxAcc, 'accno': stmtAcc.acctid, 'ledgertype': '',
                     'acctype': '', 'routineno': '', 'dayspan': 0, 'txt': '', 'curdef': statement.curdef,
                     'syncbal': round(statement.ledgerbal.balamt, 2), 'syncdate': syncdate}
            yorm.saveone('acc', anAcc)
            yorm.db.query('commit')
            return anAcc
        elif sinput == 's':
            print('Not implemented yet')
            os._exit(-1)
        else:
            os._exit(-1)
    except Exception as e:
        yorm.db.query('rollback')
        tb.print_tb(e.__traceback__)
        print(e)
        os._exit(-1)
def getOrga(sonr, exAcc):
    realname = guessOrgaName(sonr, exAcc)
    try:
        dbOrga = yorm.getmany('orga', ' where sname = "' + realname + '"')
        if dbOrga is None or len(dbOrga) == 0:
            s = input('Bank organization '+ realname + ' is not in your database. Create it automatically or select one?\n'
                      '    y: create\n'
                      '    s: select\n'
                      'other: quit\n')
            if s == 'y':
                c = yorm.db.cursor()
                c.execute('select max(orga) as orga from orga')
                r = c.fetchall()
                if r is None or len(r) == 0 or r[0] is None or r[0][0] is None:
                    maxOrg = 0
                else:
                    maxOrg = r[0][0] + 1
                anOrga = {'orga': maxOrg, 'sname': realname,
                          'url': 'https://www.' + realname + '.com', 'usr': '',
                          'password': '', 'earliest': '',
                          'txt': '', 'usrxpath': '',
                          'passxpath': '', 'loginxpath': ''}
                yorm.saveone('orga', anOrga)
                yorm.db.query('commit')
                return anOrga
            elif s == 's':
                print('Manual organization selection is not implemented yet')
                os._exit(-1)
            else:
                os._exit(-1)
        else:
            return dbOrga[0]
    except Exception as e:
        yorm.db.query('rollback')
        tb.print_tb(e.__traceback__)
        print(e)
        os._exit(-1)
def guessOrgaName(sonr, exAcc):
    shortnames = {'wf': 'WellsFargo', 'citi': 'Citibank', 'chase': 'Chase'}
    realname = None
    try:
        realname = sonr.org.lower()
    except:
        pass
    if realname is not None:
        reallongname = shortnames.get(realname)
        if reallongname is not None:
            realname = reallongname
        else:
            realname = sonr.org
    else:
        try:
            dbAccs = yorm.getmany('acc', ' where lower(substr(accno, -4, 4)) = "' + exAcc.acctid[-4:] + '"')
            for dbAcc in dbAccs:
                dbOrga = yorm.getone('orga', [dbAcc['orga']])
                s = 'Import file does not have organization name specified. \n'\
                                  + 'But an account is found probably related to the organization: \n'\
                                  + dbOrga['sname'] + ' :: ' + exAcc.acctid[-4:] + '\n'\
                                  +  '     y: Yes to use it\n'\
                                  +  '  ****: Another name to remind system\n' \
                                  +  '     q: Quit\n'
                inputOrga = input(s).strip()
                if inputOrga.lower() == 'q':
                    os._exit(-1)
                elif inputOrga.lower() == 'y':
                    realname = dbOrga['sname']
                else:
                    realname = inputOrga
                break
        except Exception as e:
            tb.print_tb(e.__traceback__)
            print(e)
            pass
        if realname is None:
            realname = input('Financial instituiton does not specify its organization name. Input one(q will exit):\n').strip()
            if realname.lower() == 'q':
                os._exit(-1)
            else:
                print('Use ' + realname + '. You have opportunity to creat it automatically if no DB record.\n')
    return realname
class TranLoader():
    def __init__(self):
        self.trans = []
        self.orgas = []
        self.accs = []
        self.statement = None
        # self.dbtransEid = yorm.getmany('trans', ' where sdate')
        # self.dbtransIndex = yorm.getmany('trans', ' ')
    def add(self, tran, orga, acc):
        self.trans.append(tran)
        self.orgas.append(orga)
        self.accs.append(acc)
    def post(self, statement, impid):
        l = len(self.trans)
        toPost = []
        toPostOrgas = []
        toPostAccs = []
        for i in range(l):
            tran = self.trans[i]
            orga = self.orgas[i]
            acc = self.accs[i]
            try:
                if tran.fitid is not None and tran.fitid != '':
                    lsTrans = yorm.getmany('trans', ' where orga = ' + str(orga['orga']) + ' and acc = ' + str(acc['acc']) + ' and earthid = "' + tran.fitid + '"')
                    if lsTrans is not None and len(lsTrans) > 0:
                        print('Duplicated found: ' + str(tran) + ' by org/account/global id. skipped')
                        continue
                ptime = tran.dtposted
                ansdate = sdate(ptime)
                curr = tran.currency or statement.curdef
                lsTrans = yorm.getmany('trans', ' where orga = ' + str(orga['orga']) + ' and acc = ' + str(acc['acc']) + ' and sdate = ' + ansdate + ' and curr = "' + curr + '" and abs(amt - ' + str(round(tran.trnamt)) + ') < 0.01')
                if lsTrans is not None and len(lsTrans) > 0:
                    print('Duplicates found: ' + tran + ' by org/account/date/curr/amt. skippied')
                    continue
                toPost.append(tran)
                toPostOrgas.append(orga)
                toPostAccs.append(acc)
            except Exception as e:
                tb.print_tb(e.__traceback__)
                print(e)
                os._exit(-1)
        if len(toPost) > 1:
            c = yorm.db.cursor()
            c.execute('select max(id) as id from trans')
            r = c.fetchall()
            if r is None or len(r) == 0 or r[0] is None or r[0][0] is None:
                maxTran = 0
            else:
                maxTran = r[0][0] + 1

            dbPosts = []
            anSdate = sdate(tran.dtposted)
            fldName = None if tran.name is None else tran.name.replace('\'', '\\\'')
            fldMemo = None if tran.memo is None else tran.memo.replace('\'', '\\\'')
            for tran in toPost:
                aDbtran = {'id': maxTran, 'orga': orga['orga'],
                           'acc': acc['acc'], 'sdate': anSdate, 'impid': impid,
                           'earthid': tran.fitid, 'ptime': round(tran.dtposted.timestamp()),
                           'amt': round(tran.trnamt, 4), 'name': fldName,
                           'memo': fldMemo, 'trantype': tran.trntype}
                if tran.currency is None or tran.currency == '':
                    aDbtran['curr'] = statement.curdef
                    aDbtran['xrate'] = None
                    aDbtran['amt'] = round(tran.trnamt, 4)
                else:
                    aDbtran['curr'] = tran.currency
                    aDbtran['xrate'] = tran.currate
                    aDbtran['amt'] = round(tran.trnamt, 4)
                dbPosts.append(aDbtran)
                maxTran = maxTran + 1
            try:
                yorm.savemany('trans', dbPosts)
                yorm.db.query('commit')
            except Exception as e:
                yorm.db.query('rollback')
                tb.print_tb(e.__traceback__)
                print(e)
                os._exit(-1)
        self.trans.clear()
def sdate(adate:datetime.datetime=None):
    if adate is not None:
        s = adate
    else:
        s = datetime.datetime.now()
    return str(s.year) + '-' + str(s.month + 100)[1:] + '-'+ str(s.day + 100)[1:]
if __name__ == '__main__':
    # mainloop()
    s = '0: Drop tables and re-init database\n' \
        + '1: Import ofx/qfx files\n' \
        + '2: Move imported file to original location\n'\
        + '3: Show config file path\n' \
          '4: quit\n'
    s1 = s
    while 1:
        i = input(s1).strip()
        if i == '0':
            dropTables()
            createTables()
            loadCfgRecs()
            s1 = s
        elif i == '1':
            tranloader = TranLoader()
            localImp(tranloader)
            s1 = s
        elif i == '2':
            moveBack()
        elif i == '3':
            s1 = s + '\n' + os.path.join(os.path.dirname(__file__), 'app.cfg\n')
        elif i == '4' or i.lower() == 'q':
            os._exit(0)
