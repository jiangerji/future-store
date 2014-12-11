#encoding=utf-8
from __future__ import unicode_literals
import json
import sys
import sqlite3
import os
import httplib
import time
import platform

import MySQLdb

import utils
from Evaluation import Evaluation
import EvaluationDeploy

def _parserEvaluation(contents):
    all = json.loads(contents)
    error_code = all.get("error_code")
    error_msg = all.get("error_msg")
    result = []
    if error_code == 0:
        # 获取成功
        data = all.get("data")
        evaluations = data.get("list")
        for evaluation in evaluations:
            _evaluation = Evaluation(evaluation)
            result.append(_evaluation)
    else:
        # 获取失败
        print "获取测评报告列表失败", error_msg

    return result

def getEvaluation(productid, limit=3):
    """
    获取3个最热的该商品的测评报告
    """
    # http://store.baidu.com/api/evaluation/list?pn=1&limit=3&type=hot&productid=1714
    url = "http://store.baidu.com/api/evaluation/list?pn=1&limit=%d&type=hot&productid=%s"%(limit, str(productid))
    allcontents = utils.requestUrlContent(url, "cache"+os.sep+"evaluation")
    evaluations = _parserEvaluation(allcontents)
    return evaluations

def _createTable(sqliteDB):
    result = True

    try:
        CREATE_COMMAND = 'CREATE  TABLE IF NOT EXISTS "evaluations" ("id" TEXT PRIMARY KEY  NOT NULL  UNIQUE , "productid" TEXT, "userid" TEXT, "title" TEXT, "score" INTEGER, "content" TEXT, "thumbnail" TEXT, "excerpt" TEXT)'
        sqliteDB.execute(CREATE_COMMAND)
    except Exception, e:
        result = False
        print "创建evaluation表异常", e

    return result

def _insertToDB(db, evaluation):
    result = True
    INSERT_COMMAND = "insert into evaluations values (?,?,?,?,?,?,?,?)"
    try:
        db.execute(INSERT_COMMAND, evaluation.toTuple())
        print "插入测评报告", evaluation.title
    except Exception, e:
        print "插入测评报告失败", evaluation.evaluationid, e
        result = False
    return result

def main(sqliteName="store.sqlite"):
    db = sqlite3.connect(sqliteName)
    db.text_factory = lambda x: unicode(x, 'utf-8', 'ignore')
    if not _createTable(db):
        return

    succcount = 0
    failcount = 0

    updateSqliteName = "_update.evaluation.sqlite"

    updateSqlite = sqlite3.connect(updateSqliteName)
    updateSqlite.text_factory = lambda x: unicode(x, 'utf-8', 'ignore')
    if not _createTable(updateSqlite):
        updateSqlite.close()
        updateSqlite = None

    # 获取product id
    cursor = db.execute("select product_id from products_info")

    for productid in cursor.fetchall():
        print "处理", productid

        evaluations = getEvaluation(productid[0])
    
        for evaluation in evaluations:
            if _insertToDB(db, evaluation):
                succcount += 1
                if _UPDATE and updateSqlite != None:
                    _insertToDB(updateSqlite, evaluation)
                    updateSqlite.commit()
            else:
                failcount += 1

        time.sleep(0.2)

    print "插入测评报告成功:", succcount
    db.commit()
    db.close()

    if _UPDATE and updateSqlite != None:
        updateSqlite.commit()
        updateSqlite.close()

        EvaluationDeploy.main(10000, -1, updateSqliteName)
    

_UPDATE = True

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

    if ("--update" in sys.argv):
        _UPDATE = True

    print "============================================"
    print "start update product:", time.asctime()

    main()

    logFile.close()  
    if oldStdout:  
        sys.stdout = oldStdout
