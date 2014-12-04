#encoding=utf-8
from __future__ import unicode_literals
import json
import sys
import sqlite3
import os
import httplib
import time

from WeissProductInfo import ProductInfo
import WeissUtils

reload(sys)
sys.setdefaultencoding('utf-8')

_FAKE = False

def parseProductList(content):
    result = []

    total_count = -1

    all = json.loads(content)
    error_code = all.get("error_code")
    error_msg = all.get("error_msg")
    if error_code == 0:
        # 获取成功
        data = all.get("data")

        total_count = data.get("total")
        product_list = data.get("list")
        for product in product_list:
            product_info = ProductInfo(product)
            result.append(product_info)
    else:
        # 获取失败
        print "获取产品列表失败，", error_msg

    return result, total_count

_HOT = 0
_SPORT = 1
_SLEEP = 5
_ROOM = 9
_CATEGORY_DICT = {
    _SPORT: ProductInfo._SPORT,
    _SLEEP: ProductInfo._HEALTHY,
    _ROOM: ProductInfo._ZNJJ
}
def getProductListByCategory(index, cat_id):
    """
    index从1开始
    cat_id: 0:热门, 1:运动, 5:睡眠, 9:客厅
    http://store.baidu.com/product/api/recommendList?cat_id=0&orderBy=hot&order=desc&pn=1&limit=36
    """
    QUOTA = 36
    conn = httplib.HTTPConnection("store.baidu.com")

    conn.request("GET", "/product/api/recommendList?cat_id=%d&orderBy=hot&order=desc&pn=%d&limit=%d"%(cat_id, index, QUOTA))
    response = conn.getresponse()
    pl = []
    total_count = -1
    if response.status:
        pl, total_count = parseProductList(response.read())

    print "获取category", cat_id, "数量", len(pl), "total", total_count
    for p in pl:
        p.setCategory(_CATEGORY_DICT[cat_id])

    return pl, total_count


def getProductList():
    db = sqlite3.connect("store.sqlite")

    TABLE_NAME = "products_info"

    try:
        CREATE_COMMAND = 'CREATE  TABLE  IF NOT EXISTS "products_info" ("product_id" INTEGER PRIMARY KEY  NOT NULL  UNIQUE , "product_name" TEXT, "product_title" TEXT, "product_intro" TEXT, "comment_count" INTEGER DEFAULT 0, "like_count" INTEGER DEFAULT 0, "product_cover_img" TEXT, "eval_num" INTEGER DEFAULT 0, "product_create_time" TEXT, "product_modified_time" TEXT, "product_price" FLOAT DEFAULT -1, "star_level" INTEGER DEFAULT 0, "product_uname" TEXT, "product_uid" TEXT, "islike" BOOL DEFAULT 0, "evaluation_count" INTEGER, "adjust_score" INTEGER DEFAULT 0, "product_thumbnail" TEXT, "category_id" TEXT)'
        db.execute(CREATE_COMMAND)

        INSERT_COMMAND = "insert into products_info values (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)"

        category_list = [_ROOM, _SPORT, _SLEEP]
        for category_id in category_list:
            index = 1
            except_count = 0
            while True:
                pl, total_count = getProductListByCategory(index, category_id)
                if total_count >= 0:
                    except_count = 0
                    for p in pl:
                        try:
                            if not _FAKE:
                                db.execute(INSERT_COMMAND, p.toTuple())
                        except Exception, e:
                            print "insert product info exception:", e

                        p.downloadImg()
                        p.downloadHtml(db)

                    index += 1
                    db.commit()

                    if len(pl) < 36:
                        print "finish get product info, cat id is", category_id
                        break
                else:
                    # 出现异常
                    except_count += 1
                    if except_count == 5:
                        index += 1
                    time.sleep(10)
    except Exception, e:
        print "create productsInfo table exception:", e

    db.commit()


if __name__ == "__main__":
    reload(sys)
    sys.setdefaultencoding('utf-8')

    workDir = os.path.dirname(os.path.realpath(sys.argv[0]))
    os.chdir(workDir)

    logFile = WeissUtils.openLogFile()

    oldStdout = sys.stdout  
    sys.stdout = logFile

    print "change work direcotory to workDir!"


    if ("--fake" in sys.argv):
        _FAKE = True

    print "============================================"
    print "start WeissProductSpider:", time.asctime()

    getProductList()

    logFile.close()  
    if oldStdout:  
        sys.stdout = oldStdout
    














