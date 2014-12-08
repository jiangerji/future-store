#encoding=utf-8
from __future__ import unicode_literals
import sys
import os
import hashlib
import sqlite3
import time
import platform
import MySQLdb

import utils

_FAKE = False

"""
主要用于给现有的加上立即购买按钮
"""

def main():
    try:
        conn = None
        if platform.system() == 'Windows':
            conn=MySQLdb.connect(host="localhost",user="root", passwd="123456",db="test",charset="utf8")
        else:
            conn=MySQLdb.connect(host="localhost",user="debian-sys-maint",passwd="eMBWzH5SIFJw5I4c",db="future-store",charset="utf8")
        cur=conn.cursor()

        sqliteDB = None
        sqliteDB = sqlite3.connect("store.sqlite")

        reseultSet = {}

        cur.execute('select id, title, introtext, `fulltext` from erji_content where catid=14 and state=1')
        for productid, title, introtext, fulltext in cur.fetchall():
            print "\n处理", productid, title
            if str(productid) != "1412" and False:
                continue

            # 如果introtext中包含了购买按钮不进行处理
            if fulltext.find("jiangerji") >= 0:
                print "  已经包含购买按钮。", 
                continue

            # 查询sqlite数据库中，是否有购买链接
            ps = sqliteDB.execute('select product_id from products_info where product_title="%s"'%title)
            ids = ps.fetchone()
            if ids == None or len(ids) <= 0:
                print "  没有在sqlite数据库中发现记录。"
                continue

            _id = ids[0]
            # 查找product url
            urls = sqliteDB.execute('select buy_url from products_view where product_id=%s'%_id)
            urls = urls.fetchone()
            if urls == None or len(urls) <= 0:
                print "  没有找到购买连接。"
                continue

            buy_url = urls[0].strip()
            if len(buy_url) > 0:
                buy_url = buy_url[0:-1].strip()

            if len(buy_url) > 0:
                print "  购买链接：", buy_url
            else:
                print "  购买链接为空。"
                continue

            # 更新fulltext
            buy_btn_code = '<p class="jiangerji"><a class="btn btn-large btn-primary" href="%s" target="_blank">立即购买</a></p>\n'%buy_url
            fulltext = buy_btn_code + fulltext
            fulltext = fulltext.replace("'", "\\'")
            updateSql = "update `erji_content` set `fulltext`='%s' where id=%s"%(fulltext, productid)
            cur.execute(updateSql)
            # cur.execute('update erji_content set `fulltext`=? where id=?', (fulltext, productid))
            print "  更新完成。"

        cur.close()
        conn.commit()
        conn.close()
    except MySQLdb.Error,e:
         print "Mysql Error %d: %s" % (e.args[0], e.args[1])


if __name__ == "__main__":
    reload(sys)
    sys.setdefaultencoding('utf-8')

    import codecs

    logFile = utils.openLogFile()

    oldStdout = sys.stdout  
    sys.stdout = logFile

    if ("--fake" in sys.argv):
        _FAKE = True

    main()

    logFile.close()  
    if oldStdout:  
        sys.stdout = oldStdout