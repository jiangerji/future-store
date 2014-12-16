#encoding=utf-8
from __future__ import unicode_literals
import sys
import os
import time
import platform
import MySQLdb

import utils

_FAKE = False

def aliasVerify(alias):
    _special_chars = "\\/"
    # alias = alias.replace("-", "").strip()
    for i in _special_chars:
        alias = alias.replace(i, "-")

    if alias[0] == '-':
        alias = alias[1:]
    return alias

def verifyAlias():
    print "===================Start Verify Alias==================="
    mysqlConn = None
    mysqlCur = None
    try:
        if platform.system() == 'Windows':
            mysqlConn=MySQLdb.connect(host="localhost",user="root", passwd="123456",db="test",charset="utf8")
        else:
            mysqlConn=MySQLdb.connect(host="localhost",user=utils.MYSQL_PASSPORT,passwd=utils.MYSQL_PASSWORD,db=utils.MYSQL_DATABASE,charset="utf8")
        mysqlCur=mysqlConn.cursor()
    except MySQLdb.Error,e:
         print "Mysql Error %d: %s" % (e.args[0], e.args[1])

    if mysqlCur != None:
        mysqlCur.execute('select id, title, alias from erji_content where state=1')
        for (_id, _title, _alias) in mysqlCur.fetchall():
            alias = aliasVerify(_alias)
            if _alias != alias:
                # print "%s-%s"%(_id, _alias)
                # print _id, alias
                mysqlCur.execute('update erji_content set alias="%s" where id=%s'%(alias, _id))
                print "  Update", _id, "alias from", _alias, "to", alias

        mysqlConn.commit()
        mysqlCur.close()
        mysqlConn.close()

if __name__ == "__main__":
    reload(sys)
    sys.setdefaultencoding('utf-8')

    workDir = os.path.dirname(os.path.realpath(sys.argv[0]))
    os.chdir(workDir)

    logFile = utils.openLogFile()

    oldStdout = sys.stdout  
    sys.stdout = logFile

    print "change work direcotory to workDir", workDir

    if ("--fake" in sys.argv):
        _FAKE = True

    print "============================================"
    print "start ArticleUtils:", time.asctime()

    verifyAlias()

    logFile.close()  
    if oldStdout:  
        sys.stdout = oldStdout