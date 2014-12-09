#encoding=utf-8
from __future__ import unicode_literals
import sys
import os
import hashlib
import sqlite3
import time

import MySQLdb

import utils

def insertEvaluation(cursor, quota=1, ignore=-1, _sqliteName=None):
    sqliteName = "store.sqlite"
    if _sqliteName != None:
        sqliteName = _sqliteName

    db = sqlite3.connect(sqliteName)
    allEvaluations = db.execute('select id, productid, title, content, thumbnail, excerpt from evaluations').fetchall()

    count = 0
    ignore_count = 0

    for evaluation in allEvaluations:
        ignore_count += 1
        if ignore_count <= ignore:
            continue

        evaluation_id, product_id, title, content, thumbnail, excerpt = evaluation
        print "\n处理", evaluation_id, title

        # 获取buy url
        buy_url = ""
        try:
            buy_url = db.execute('select buy_url from products_view where product_id='+product_id).fetchone()[0]
        except Exception, e:
            pass

        # images是 erji_tz_portfolio_xref_content需要
        if thumbnail != None:
            images = utils.downloadNewsThumbnails(product_id, thumbnail)
            print "insert images", images
            if images == None:
                print "下载", thumbnails, "失败！"

        asset_id = utils.insertIntoAssets(cursor, title)

        # 添加原文链接
        origin_text_url = "http://store.baidu.com/evaluation/view/%s.html"%str(evaluation_id)
        origin_text_btn_code = '<a class="btn btn-large btn-primary" href="%s" target="_blank">测评原文地址</a>\n'%origin_text_url

        additionContent = origin_text_btn_code

        if len(buy_url) > 0:
            buy_btn_code = '<a class="btn btn-large btn-primary" href="%s" target="_blank">立即购买</a>\n'%buy_url
            additionContent = buy_btn_code + additionContent

        content = '<p class="jiangerji">'+additionContent+'</p>' + content

        content_id = utils.insertIntoContent(cursor, asset_id, title, excerpt, content, 15)
        if content_id <= 0:
            continue

        count += 1
        if count >= quota:
            break

def main(quota=1, ignore=-1, _sqliteName="store.sqlite"):
    try:
        import platform
        conn = None
        if platform.system() == 'Windows':
            conn=MySQLdb.connect(host="localhost",user="root", passwd="123456",db="test",charset="utf8")
        else:
            conn=MySQLdb.connect(host="localhost",user=utils.MYSQL_PASSPORT,passwd=utils.MYSQL_PASSWORD,db=utils.MYSQL_DATABASE,charset="utf8")
        cur=conn.cursor()

        insertEvaluation(cur, quota, ignore, _sqliteName)

        cur.close()
        conn.commit()
        conn.close()
    except MySQLdb.Error,e:
         print "Mysql Error %d: %s" % (e.args[0], e.args[1])

if __name__ == "__main__":
    reload(sys)
    sys.setdefaultencoding('utf-8')

    workDir = os.path.dirname(os.path.realpath(sys.argv[0]))
    os.chdir(workDir)

    logFile = utils.openLogFile()

    oldStdout = sys.stdout  
    sys.stdout = logFile

    print "change work direcotory to workDir", workDir

    count = 1
    ignore = -1

    if ("--fake" in sys.argv):
        _FAKE = True

    if len(sys.argv) > 1:
        count = abs(int(sys.argv[1]))


    if len(sys.argv) > 2:
        ignore = int(sys.argv[2])

    print "============================================"
    print "start deploy evaluation:", time.asctime(), count

    main(count, ignore)

    logFile.close()  
    if oldStdout:  
        sys.stdout = oldStdout