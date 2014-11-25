#encoding=utf-8
from __future__ import unicode_literals
import sys
import os
import hashlib
import sqlite3
import time
import Image

from utils import *

def insertArtical(cursor, quota=1, ignore=-1):
    db = sqlite3.connect("store.sqlite")
    allProducts = db.execute('select product_id, product_title, product_intro, product_cover_img, product_thumbnail from products_info').fetchall()

    count = 0
    ignore_count = 0

    for product in allProducts:
        ignore_count += 1
        if ignore_count <= ignore:
            continue

        # _id, title, introtext, thumbnails = news
        product_id, product_title, product_intro, product_cover_img, product_thumbnail = product
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
        images = downloadNewsThumbnails(product_id, thumbnails)
        print "insert images", images
        if images == None:
            print "下载", thumbnails, "失败！"
            continue

        asset_id = insertIntoAssets(cursor, product_title)


        # 获取full text
        full_text = db.execute('select product_detail from products_view where product_id='+str(product_id)).fetchone()[0]
        content_id = insertIntoContent(cursor, asset_id, product_title, product_intro, full_text, 14)

        if content_id <= 0:
            continue

        insert_xref_content(cursor, content_id, images)

        count += 1
        if count >= quota:
            break

def insert_article_main(quota=1, ignore=-1):
    
    try:
        import platform
        conn = None
        if platform.system() == 'Windows':
            conn=MySQLdb.connect(host="localhost",user="root", passwd="123456",db="world",charset="utf8")
        else:
            conn=MySQLdb.connect(host="localhost",user="debian-sys-maint",passwd="eMBWzH5SIFJw5I4c",db="future-store",charset="utf8")
        cur=conn.cursor()

        insertArtical(cur, quota, ignore)

        cur.close()
        conn.commit()
        conn.close()
    except MySQLdb.Error,e:
         print "Mysql Error %d: %s" % (e.args[0], e.args[1])

if __name__ == "__main__":
    reload(sys)
    sys.setdefaultencoding('utf-8')

    insert_article_main()
    # insertArtical(None, 100000)