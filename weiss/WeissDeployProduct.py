#encoding=utf-8
from __future__ import unicode_literals
import sys
import os
import hashlib
import sqlite3
import time
import Image

import WeissConstants
import WeissUtils

import MySQLdb

def insertProduct(cursor, quota=1, ignore=-1, _sqliteName=None):
    sqliteName = "store.sqlite"
    if _sqliteName != None:
        sqliteName = _sqliteName

    db = sqlite3.connect(sqliteName)
    allProducts = db.execute('select product_id, product_title, product_intro, product_cover_img, product_thumbnail, category_id from products_info').fetchall()

    count = 0
    ignore_count = 0

    for product in allProducts:
        ignore_count += 1
        if ignore_count <= ignore:
            continue

        # _id, title, introtext, thumbnails = news
        product_id, product_title, product_intro, product_cover_img, product_thumbnail, category_id = product
        # print product_id, product_title, product_intro, product_cover_img, product_thumbnail

        thumbnails = None
        if product_cover_img != None and len(product_cover_img.strip()) > 0:
            thumbnails = product_cover_img
        else:
            try:
                thumbnails = eval(product_thumbnail)[0]
            except Exception, e:
                pass

        if thumbnails == None:
            print "未找到图片，跳过", product_id
            continue

        # print "thumbnails", thumbnails
            

        # images是 erji_tz_portfolio_xref_content需要
        images = WeissUtils.downloadNewsThumbnails(product_id, thumbnails)
        print "insert images", images
        if images == None:
            print "下载", thumbnails, "失败！"
            continue

        asset_id = WeissUtils.insertIntoAssets(cursor, product_title)

        # 获取full text
        product_intro, full_text = db.execute('select product_intro, product_detail from products_view where product_id='+str(product_id)).fetchone()
        content_id = WeissUtils.insertIntoContent(cursor, asset_id, product_title, product_intro, full_text, category_id)

        if content_id <= 0:
            continue

        WeissUtils.insert_xref_content(cursor, content_id, images)

        count += 1
        if count >= quota:
            break

def insert_product_main(quota=1, ignore=-1, _sqliteName="store.sqlite"):
    
    try:
        import platform
        conn = None
        if platform.system() == 'Windows':
            conn=MySQLdb.connect(host="localhost",user="root", passwd="123456",db="test",charset="utf8")
        else:
            conn=MySQLdb.connect(host="localhost",user=WeissConstants.MYSQL_PASSPORT,passwd=WeissConstants.MYSQL_PASSWORD,db=WeissConstants.MYSQL_DATABASE,charset="utf8")
        cur=conn.cursor()

        insertProduct(cur, quota, ignore, _sqliteName)

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

    logFile = WeissUtils.openLogFile()

    oldStdout = sys.stdout  
    sys.stdout = logFile

    count = 1
    ignore = -1

    if ("--fake" in sys.argv):
        _FAKE = True

    if len(sys.argv) > 1:
        count = abs(int(sys.argv[1]))


    if len(sys.argv) > 2:
        ignore = int(sys.argv[2])

    print "============================================"
    print "start update product:", time.asctime(), count

    insert_product_main(count, ignore)

    logFile.close()  
    if oldStdout:  
        sys.stdout = oldStdout