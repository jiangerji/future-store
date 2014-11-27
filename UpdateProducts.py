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

from productInfo import ProductInfo
from utils import *
from ProductSpider import parseProductList
from DeployProducts import insert_product_main

_FAKE = False

def updateProductListByHot(quota=1):
    """
    http://store.baidu.com/product/api/recommendList?cat_id=0&orderBy=hot&order=desc&pn=1&limit=36
    """
    db = sqlite3.connect("store.sqlite")
    updateDB = sqlite3.connect("update.store.sqlite")

    TABLE_NAME = "products_info"

    try:
        CREATE_COMMAND = 'CREATE  TABLE  IF NOT EXISTS "products_info" ("product_id" INTEGER PRIMARY KEY  NOT NULL  UNIQUE , "product_name" TEXT, "product_title" TEXT, "product_intro" TEXT, "comment_count" INTEGER DEFAULT 0, "like_count" INTEGER DEFAULT 0, "product_cover_img" TEXT, "eval_num" INTEGER DEFAULT 0, "product_create_time" TEXT, "product_modified_time" TEXT, "product_price" FLOAT DEFAULT -1, "star_level" INTEGER DEFAULT 0, "product_uname" TEXT, "product_uid" TEXT, "islike" BOOL DEFAULT 0, "evaluation_count" INTEGER, "adjust_score" INTEGER DEFAULT 0, "product_thumbnail" TEXT)'
        db.execute(CREATE_COMMAND)
        updateDB.execute(CREATE_COMMAND)

        INSERT_COMMAND = "insert into products_info values (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)"

        QUOTA = 36
        index = 1
        conn = httplib.HTTPConnection("store.baidu.com")
        except_count = 0
        succ_count = 0
        while True or index == 1:
            conn.request("GET", "/product/api/recommendList?cat_id=0&orderBy=hot&order=desc&pn=%d&limit=%d"%(index, QUOTA))
            response = conn.getresponse()
            if response.status:
                except_count = 0
                pl, total_count = parseProductList(response.read())

                for p in pl:
                    try:
                        db.execute(INSERT_COMMAND, p.toTuple())
                        updateDB.execute(INSERT_COMMAND, p.toTuple())

                        succ_count += 1
                        # 插入成功，缓存图片和html
                        p.downloadImg()
                        p.downloadHtml(db)
                        p.downloadHtml(updateDB)
                    except Exception, e:
                        print "insert product info exception:", e

                    if succ_count >= quota:
                        break

                # 超过希望处理数量，退出
                if succ_count >= quota:
                    break

                index += 1
                if not _FAKE:
                    db.commit()

                if len(pl) < QUOTA:
                    print "finish get product info!"
                    break

                try:
                    db_count = db.execute("SELECT count(*) from products_info").fetchall()[0][0]
                    if total_count > 0 and db_count >= int(total_count):
                        print "product info already full!"
                        break
                except Exception, e:
                    pass

                time.sleep(1)
            else:
                except_count += 1
                if except_count == 5:
                    index += 1
                time.sleep(10)
    except Exception, e:
        print "create productsInfo table exception:", e

    if not _FAKE:
        db.commit()

    updateDB.commit()
    updateDB.close()
    insert_product_main(10000, -1, "update.store.sqlite")

    os.remove("update.store.sqlite")


if __name__ == "__main__":
    reload(sys)
    sys.setdefaultencoding('utf-8')

    import codecs

    logFile = codecs.open("UpdateProducts.log", "w", "utf-8")

    oldStdout = sys.stdout  
    sys.stdout = logFile

    count = 1000
    ignore = -1

    if ("--fake" in sys.argv):
        _FAKE = True

    if len(sys.argv) > 1:
        count = abs(int(sys.argv[1]))


    if len(sys.argv) > 2:
        ignore = int(sys.argv[2])

    updateProductListByHot(count)

    logFile.close()  
    if oldStdout:  
        sys.stdout = oldStdout