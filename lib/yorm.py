# from MySQLdb import _mysql, cursors
import MySQLdb
class Yorm:
    def __init__(self, config={}):
        self.db = MySQLdb.connect(host=config["host"],user=config["user"],passwd=config["passwd"],db=config["db"])
        self.numtypes = ["int", "tinyint", "bigint", "double", "decimal", "smalint", "float"]
        self.strtypeTable = 1
        self.strtypeType = 2
        self.printwarning = False if config.get('printwarning') == None else config.get('printwarning')
        self.batchsize = 20 if config.get('options') is None else 20 if config.get('options').get('batchSize') is None else config.get('options').get('batchSize')
        self.database = config['db']
        self.tbldefs = None
        self.tbldefs = self.bufferinit()

    def bufferinit(self, doinit=False):
        if not doinit and self.tbldefs != None:
            return self.tbldefs
        result = {}
        pros = []
        tblarrs = []
        tblarr = None
        buflist = []
        c = None
        try:
            c = self.db.cursor(MySQLdb.cursors.DictCursor)
            c.execute('select table_name as tn from information_schema.tables where table_schema = "' + self.database + '"')
            if c.rowcount < 1:
                return None
            rows = c.fetchall()
            for i in range(0, c.rowcount):
                if i%self.batchsize == 0:
                    if i > 0:
                        tblarrs.append(tblarr)
                    tblarr = []
                tblarr.append(rows[i]['tn'])
            tblarrs.append(tblarr)
            sselectdef = "select table_name as tn, column_name as cn, column_type as ct, data_type as dt, column_key as ck";
            sfromdef = " from information_schema.columns";
            swheredef = None
            for atblarr in tblarrs:
                swheredef = ' where table_schema = "' + self.database + '" and  table_name in (';
                for atbl in atblarr:
                    swheredef = swheredef + "'" + atbl + "', "
                swheredef = swheredef[0: len(swheredef) - 2] + ") order by tn"
                ssqldef = sselectdef + sfromdef + swheredef
                c1 = self.db.cursor(MySQLdb.cursors.DictCursor)
                try:
                    c1.execute(ssqldef)
                    cols = {}
                    pricols = {}
                    swhere = " where "
                    sselect = "select "
                    sfrom = ""
                    currtn = None
                    lasttn = ""

                    rows1 = c1.fetchall()
                    for j in range(0, c1.rowcount):
                        currtn = rows1[j]['tn']
                        if (currtn != lasttn):
                            if j > 0:
                                swhere = swhere[0: len(swhere) - 4]
                                sselect = sselect[0: len(sselect) - 2]
                                sfrom = " from " + lasttn
                                result[lasttn] = {}
                                result[lasttn]['strtype'] = self.strtypeTable
                                result[lasttn]['cols'] = cols
                                result[lasttn]['swhere'] = swhere
                                result[lasttn]['sselect'] = sselect
                                result[lasttn]['sfrom'] = sfrom
                                result[lasttn]['pricols'] = pricols
                            cols = {}
                            pricols = []
                            swhere = " where "
                            sselect = "select "
                        cols[rows1[j]['cn']] = rows1[j]
                        if rows1[j]['ck'].lower() == 'pri':
                            swhere = swhere + " " + rows1[j]['cn'] + ' = %s and '
                            pricols.append(rows1[j]['cn'])
                        sselect = sselect + rows1[j]['cn'] + ', '
                        lasttn = currtn
                    swhere = swhere[0: len(swhere) - 4]
                    sselect = sselect[0: len(sselect) - 2]
                    sfrom = ' from ' + lasttn
                    result[lasttn] = {}
                    result[lasttn]["strtype"] = self.strtypeTable
                    result[lasttn]["cols"] = cols
                    result[lasttn]["swhere"] = swhere
                    result[lasttn]["sselect"] = sselect
                    result[lasttn]["sfrom"] = sfrom
                    result[lasttn]["pricols"] = pricols
                except Exception as e1:
                    raise e1
                finally:
                    if not c1:
                        c1.close()
            return result
        except Exception as e:
            raise e
        finally:
            if not c:
                c.close()


    def tyepdef(self, typename, flds):
        tbldefs = self.tbldefs
        try:
            if tbldefs == None:
                raise Exception('Please specify tables definition object')
            if tbldefs[typename] != None:
                raise Exception(typename + ' is defined already')
            else:
                typecols = []
                for afld in flds:
                    if afld['ref'] != None:
                        aref = afld['ref'].split['.']
                        tbl = aref[0]
                        fld = aref[1]
                        typecols.append(tbldefs[tbl]['cols'][fld])
                    else:
                        if afld['dt'] == None:
                            raise Exception("Please either refering to db definition or define datatype with 'dt' for field " + afld['cn'])
                        if afld['ct'] == None:
                            raise Exception("Please either refering to db definition or define datatype with 'ct' for field " + afld['cn'])
                        typecols.append(afld)
                tbldefs[typename] = {}
                tbldefs[typename]['strtype'] = self.strtypeType
                tbldefs[typename]['cols'] = typecols
                return tbldefs[typename]
        except Exception as e:
            raise e

    def getone(self, tn, objkey):
        tbldef = self.tbldefs[tn]
        ssql = None
        c = None
        try:
            keyarr = []
            if objkey != None and type(objkey) is dict:
                for i in range(len(tbldef['pricols'])):
                    keyarr.append(objkey[tbldef['pricols'][i]])
            elif objkey != None:
                keyarr = objkey
            else:
                raise Exception('Must give primary key values (either array or dictionary)')
            ssql = tbldef['sselect'] + tbldef['sfrom'] + tbldef['swhere']
            c = self.db.cursor(MySQLdb.cursors.DictCursor)
            c.execute(ssql, keyarr)
            if c.rowcount < 1:
                raise Exception('Nothing found')
            return c.fetchall()[0]
        except Exception as e:
            print('Select statement failed in getone: ' + ssql)
            raise e
        finally:
            if not c:
                c.close()

    def getmany(self, tn, sfilter='', curDict=True):
        tbldef = self.tbldefs[tn]
        ssql = None
        realfilter = '' if sfilter is None else sfilter
        c = None
        try:
            ssql = tbldef['sselect'] + tbldef['sfrom'] + realfilter
            if curDict:
                c = self.db.cursor(MySQLdb.cursors.DictCursor)
            else:
                c = self.db.cursor()
            c.execute(ssql)
            r = c.fetchall()
            if len(r) == 0 and self.printwarning:
                print('Warning: zeros records selected: ', ssql)
            return r
        except Exception as e:
            print('Failed getmany sql: ' + ssql)
            raise e
        finally:
            if not c:
                c.close()
    def getbytype(self, typename, ssql):
        adef = self.tbldefs[typename]
        result = []
        one = None
        try:
            c = self.db.cursor(MySQLdb.cursors.DictCursor)
            c.execute(ssql)
            rows = c.fetchall()
            for row in rows:
                one = {}
                for cn in adef['cols']:
                    if row[cn] != None:
                        one[cn] = row[cn]
                result.append(one)
            return result
        except Exception as e:
            raise e
    def saveone(self, tn, one, insertOrReqplace=True):
        tbldef = self.tbldefs[tn]
        ssave = 'insert into ' + tn if insertOrReqplace else 'replace into ' + tn
        sfld = ' ('
        sval = ' values ('
        cols0 = tbldef['cols']
        cols = []
        colsname = []
        pricols = tbldef['pricols']
        for k, v in one.items():
            if cols0[k] != None:
                cols.append(cols0[k])
                colsname.append(k)
        for pricol in pricols:
            if pricol not in colsname:
                raise Exception('Key missing for table/key: ' + tn + '/' + pricol)
        for key in cols0:
            if key not in colsname:
                # Meaning some db column name not in object properties
                # Todo: Log either info or warning messages is quite necessary
                continue
            sfld = sfld + key + ', '
            dt = cols0[key]['dt']
            if one[key] != None:
                if dt not in self.numtypes:
                    sval = sval + "'" + one[key] + "', "
                else:
                    try:
                        float(one[key])
                        sval = sval + str(one[key]) + ', '
                    except:
                        raise Exception('Data type is not right: ' + tn + '/' + key + ':' + str(one[key]))
            else:
                sval = sval + 'null, '

        sfld = sfld[0: len(sfld) - 2] + ') '
        sval = sval[0: len(sval) - 2] + ') '

        ssql = ssave + sfld + sval
        try:
            self.db.query(ssql)
        except Exception as e:
            print('Yorm saveone error, sql: ' + ssql)
            raise e
    def savemany(self, tn, objs, pbatchsize=100, insertOrUpdate=True):
        if objs == None or len(objs) == 0:
            raise Exception('Nothing to save for table ' + tn + ' in Yorm savemany')
        tbldef = self.tbldefs[tn]
        ssave = 'insert into ' + tn if insertOrUpdate else 'replace into ' + tn
        sflds = ' ('
        svalueses = 'values '
        arrvalueses = []
        tblcols = tbldef['cols']

        for k, v in objs[0].items():
            if tblcols.get(k) is not None:
                sflds = sflds + k + ', '
        for i in range(len(objs)):
            if (i % pbatchsize) == 0:
                if i > 0:
                    svalueses = svalueses[0: len(svalueses) - 1]
                    arrvalueses.append(svalueses)
                svalueses = 'values '
            one = objs[i]
            svaluesone = '('
            for k, v in one.items():
                if tblcols.get(k) != None:
                    dt = tblcols[k]['dt']
                    if one[k] != None:
                        if dt not in self.numtypes:
                            try:
                                svaluesone = svaluesone + "'" + one[k] + "', "
                            except Exception as ef:
                                raise Exception(tn + '.' + k + ' value string required. Value encounted: ' + str(one[k]))
                        else:
                            try:
                                float(one[k])
                            except Exception as ef:
                                raise Exception(tn + '.' + k + ' must be numeric. But value encountered: ' + str(one[k]))
                            svaluesone = svaluesone + str(one[k]) + ', '
                    else:
                        svaluesone = svaluesone + 'null, '
            svaluesone = svaluesone[0: len(svaluesone) - 2] + '),';
            svalueses = svalueses + svaluesone
        sflds = sflds[0: len(sflds) - 2] + ')'
        svalueses = svalueses[0: len(svalueses) - 1]
        arrvalueses.append(svalueses)
        try:
            for arrvalues in arrvalueses:
                ssql = ssave + sflds + arrvalues
                self.db.query(ssql)
        except Exception as e:
            print('Failed sql statement savemany(): ' + ssql)
            print(e)
            raise e

if __name__ == '__main__':
    yorm = None
    try:
        yorm = Yorm()
        a = {'a': '8', 'bv': '120', 'b': 3}
        yorm.saveone('a', a, False)
        manya = []
        for i in range(1, 5):
            acopy = a.copy()
            acopy['a'] = str(float(acopy['a']) + i)
            manya.append(acopy)
        yorm.savemany('a', manya, insertOrUpdate=False)
        yorm.db.query('commit')
    except Exception as e:
        print(e)
        yorm.db.query('rollback')
        print('Rolledback')
    bs = yorm.getmany('a', '')
    for b in bs:
        print(b)
    rec = yorm.getone('a', [9])
    print(rec)
