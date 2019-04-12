import ofxparse
import traceback as tb
import warnings
from lib.gv import yorm
import re
import bs4
import feedparser
import copy
from lxml import etree
class OFX_HEADER():
    def __init__(self):
        self.OFXHEADER = None
        self.DATA = None
        self.VERSION = None
        self.SECURITY = None
        self.ENCODING = None
        self.HEADER_CHARSET = None
        self.COMPRESSION = None
        self.OLDFILEUID = None
        self.NEWFILEUID = None
class OFX_ACCOUNT():
    def __init__(self):
        self.fiorg = None
        self.acc = None
        self.accno = None
        self.acctype = None
        self.routine = None
        self.curdef = None
    def getDbOrga(self):
        shortnames = {'wf': ['wellsfargo'], 'citi': ['citibank']}
        sname = shortnames.get(self.fiorg)
        if sname is not None:
            orgas = yorm.getmany('orga', 'where sname = "' + sname + '"')
            if orgas is not None and len(orgas) == 1:
                return orgas[0]
        warnings.warn('No organization found for short name: ', self.fiorg)
        return None
    def getDbAcc(self, orga):
        try:
            cnt = 0
            selfLast4 = self.accno[-4:]
            theAcc = None
            accs = yorm.getmany('acc', ' where orga = ' + str(orga['orga']))
            for acc in accs:
                accLast4 = acc['accno'][-4:]
                if selfLast4 == accLast4:
                    cnt = cnt + 1
                    theAcc = acc
            if cnt > 1:
                raise Exception('More than one account found matching last 4 digits of account no in your database: ', selfLast4)
            if cnt == 0:
                warnings.warn('No account found matching last 4 digits of account no in your database: ', selfLast4)
            return theAcc
        except Exception as e:
            tb.print_tb(e.__traceback__)
            print(e)
class OFX():
    def __init__(self):
        self.accounts:[OFX_ACCOUNT] = []
        self.account:OFX_ACCOUNT = None
        self.statement = None
        self.transactions = None
        self.header:OFX_HEADER = OFX_HEADER()
        self.orgashortname = None
class Node():
    def __init__(self):
        self.parent = None
        self.children = None
    def addNode(self, parent=None, rightBro=None):
        if parent is not None:
            if parent.children is not None:
                if rightBro is None:
                    parent.children.append(self)
                else:
                    for i in range(len(parent.children)):
                        if parent.children[i] == rightBro:
                            ls = parent.children[:i] + [self] + parent.children[i+1:]
                            parent.children.clear()
                            parent.children.extend(ls)
            else:
                parent.children = [self]
        else:
            warnings.warn('You are trying to add this node to a Null parent')
    def getRoot(self):
        up = self
        while 1:
            lv = up.parent()
            if lv is None:
                return up
            else:
                up = lv
    def cutBranch(self, node):
        parent = node.parent
        if parent is None:
            warnings.warn('You are trying to cut a branch node but it is root')
            return
        if parent.chilren is None:
            warnings.warn('You are trying to cut a branch node but it is not in its parent children')
            return
        if node not in (parent.chilren):
            warnings.warn('You are trying to cut a branch node but it is not in its parent children')
            return
        parent.children.remove(node)
    def getNode(self, path):
        node = self
        lp = len(path)
        for i in range(lp):
            if node.children is None or i < 0 or i >= lp:
                return None
            node = node.children[i]
        return node
    @classmethod
    def getNextPath(path, root=None, up=False):
        thisNode = root.getNode(path)
        if thisNode is None:
            while len(path) > 0:
                if thisNode is None:
                    path = path.pop(-1)
                    thisNode = root.getNode(path)
                else:
                    return Node.getNextPath(path, root = root)
        else:
            if len(path) == 0:
                if root.children is None:
                    return None
                else:
                    return root.children[0]
            if thisNode.children is None or len(thisNode.children) == 0:
                path[-1] = path[-1] + 1
                thisNode = thisNode.parent.children[path[-1]]
                if thisNode is not None:
                    return path
                path = path.pop(-1)
                return Node.getNextPath(path, root = root, up=True)
            elif up:
                path[-1] = path[-1] + 1
                thisNode = root.getNode(path)
                if thisNode is not None:
                    return path
                path.pop(-1)
                return Node.getNextPath(path, root=root, up=True)
            else:
                path = path.append(0)
                return path

class QFXParser():
    HEADER_OFXHEADER = 'OFXHEADER'
    HEADER_DATA = 'DATA'
    HEADER_VERSION = 'VERSION'
    HEADER_SECURITY = 'SECURITY'
    HEADER_ENCODING = 'ENCODING'
    HEADER_CHARSET = 'CHARSET'
    HEADER_COMPRESSION = 'COMPRESSION'
    HEADER_OLDFILEUID = 'OLDFILEUID'
    HEADER_NEWFILEUID = 'NEWFILEUID'
    TAG_OFX = 'OFX'
    TAG_SIGNONMSGSRSV1 = 'SIGNONMSGSRSV1'
    TAG_SONRS = 'SONRS'
    TAG_STATUS = 'STATUS'
    TAG_CODE = 'CODE'
    TAG_SEVERITY = 'SEVERITY'
    TAG_DTSERVER = 'DTSERVER'
    TAG_LANGUAGE = 'LANGUAGE'
    TAG_FI = 'FI'
    TAG_ORG = 'ORG'
    TAG_INTU_BID = 'INTU.BID'
    TAG_CREDITCARDMSGSRSV1 = 'CREDITCARDMSGSRSV1'
    TAG_CCSTMTTRNRS = 'CCSTMTTRNRS'
    TAG_TRNUID = 'TRNUID'
    TAG_MESSAGE = 'MESSAGE'
    TAG_CCSTMTRS = 'CCSTMTRS'
    TAG_CURDEF = 'CURDEF'
    TAG_CCACCTFROM = 'CCACCTFROM'
    TAG_ACCTID = 'ACCTID'
    TAG_BANKTRANLIST = 'BANKTRANLIST'
    TAG_DTSTART = 'DTSTART'
    TAG_DTEND = 'DTEND'
    TAG_STMTTRN = 'STMTTRN'
    TAG_TRNTYPE = 'TRNTYPE'
    TAG_DTPOSTED = 'DTPOSTED'
    TAG_TRNAMT = 'TRNAMT'
    TAG_FITID = 'FITID'
    TAG_NAME = 'NAME'
    TAG_LEDGERBAL = 'LEDGERBAL'
    TAG_BALAMT = 'BALAMT'
    TAG_DTASOF = 'DTASOF'
    TAG_AVAILBAL = 'AVAILBAL'
    def __init__(self):
        lineDiv = re.compile(r'[\r\n]')
        headerDiv = re.compile(r':')
        tagDiv = re.compile(r'>')
        valDiv = re.compile(r':')
    def parseFeed(self, s):
        root = {}
        path = []
        a = self.yparse(s, root, path, i=0)
        return a
    def yparse1(self, s, node, path, i):
        intag = False
        atag = None
        aVal = None
        while 1:
            if i > len(s):
                break
            aChar = s[i]
            if intag:
                if aChar == '>':
                    intag = False
                    aval = ''
                else:
                    atag = atag + aChar
            else:
                if aChar == '<':
                    if s[i + 1] == '/':
                        for j in range(len(path)):
                            k = 0 - j - 1
                    else:
                        intag = True
                        path.append({})
                        atag = ''
                else:
                    aval = aval + aChar

    def parse(self, s):
        print('-------------Parsing')
        ofx = OFX()
        try:
            sa = self.lineDiv.split(s)
            currPath = []
            for line0 in sa:
                line = line0.strip()
                if line[0] != '<':
                    saheader = self.headerDiv.split(line)
                    if len(saheader) == 2:
                        try:
                            self.header.__setattr__(saheader[0], saheader[1])
                        except Exception as e:
                            tb.print_tb(e.__traceback__)
                            print(e)
                    else:
                        print('Cannot understand a header line: ', line)
                else:
                    saline = self.tagDiv.split(line)
                    if saline[0][1] != '/':
                        currPath = currPath.append(saline[0][1:])
                        self.processLine(currPath, saline)
                    else:
                        npath = -1
                        while 1:
                            if npath < 0 - len(currPath):
                                break
                            if currPath[npath] == saline[0][1:]:
                                currPath = currPath[:npath]
                                break

        except Exception as e:
            tb.print_tb(e.__traceback__)
            print(e)
    def processLine(self, ofx:OFX, currPath, saline):
        if currPath[-1] == QFXParser.TAG_ORG:
            if currPath[-2] == QFXParser.TAG_FI:
                ofx.orgashortname = saline[1]
        if currPath[-1] == QFXParser.TAG_ACCTID:
            if currPath[-2] == QFXParser.TAG_CCACCTFROM:
                ofx.account.accno = saline[1]
    def yparse(self, s):
        parser = etree.HTMLParser()
        theDoc = etree.fromstring(s, parser)
        # print(theDoc.iterchildren)
        for kid in theDoc.iterchildren():
            print(dir(kid))
            for kkid in kid.iterchildren():
                print(dir(kkid))
                print(kkid.tag)
                for kkkid in kkid.iterchildren():
                    print(kkkid.tag)
        return theDoc