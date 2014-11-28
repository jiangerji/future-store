#encoding=utf-8
from __future__ import unicode_literals

import sys
import re
import sqlite3

from DownloadManager import *
from utils import *
import Tags

class ProductInfo:

    def _init(self):
        self.product_id = -1
        self.product_name = ""
        self.product_title = ""
        self.product_intro = ""
        self.comment_count = 0
        self.like_count = 0
        self.product_cover_img = ""
        self.eval_num = 0
        self.product_create_time = ""
        self.product_modified_time = ""
        self.product_thumbnail = []
        self.product_price = ""
        self.star_level = ""
        self.product_uname = ""
        self.product_uid = ""
        self.islike = False
        self.evaluation_count = 0
        self.adjust_score = 0

    def __str__(self):
        result = []
        result.append("Product Info:")
        result.append("  product id: %s"%str(self.product_id))
        result.append("  product name: %s"%str(self.product_name))
        result.append("  product title: %s"%str(self.product_title))
        result.append("  product intro: %s"%str(self.product_intro))
        result.append("  comment count: %s"%str(self.comment_count))
        result.append("  like count: %s"%str(self.like_count))
        result.append("  product cover img: %s"%str(self.product_cover_img))
        result.append("  eval num: %s"%str(self.eval_num))
        result.append("  product create time: %s"%str(self.product_create_time))
        result.append("  product modified time: %s"%str(self.product_modified_time))
        result.append("  product price: %s"%str(self.product_price))
        result.append("  star level: %s"%str(self.star_level))
        result.append("  product uname: %s"%str(self.product_uname))
        result.append("  product uid: %s"%str(self.product_uid))
        result.append("  is like: %s"%str(self.islike))
        result.append("  evaluation count: %s"%str(self.evaluation_count))
        result.append("  adjust score: %s"%str(self.adjust_score))
        result.append("  product thumbnail:")
        for i in self.product_thumbnail:
            result.append("    %s"%str(i))

        return "\n".join(result)

    def __init__(self, infos):
        cache_dir = os.path.join("cache", "product")
        self.html_cache_dir = os.path.join(cache_dir, "html")
        if not os.path.isdir(self.html_cache_dir):
            os.makedirs(self.html_cache_dir)

        # print "创建缓存目录", self.html_cache_dir

        self.img_cache_dir = os.path.join(cache_dir, "img")
        if not os.path.isdir(self.img_cache_dir):
            os.makedirs(self.img_cache_dir)

        # infos is a dict
        if type(infos) != type({}):
            self._init()
            return
        self.product_id = infos.get("product_id", -1)
        self.product_name = infos.get("product_name", "")
        self.product_title = infos.get("product_title", "")
        self.product_intro = infos.get("product_intro", "")
        self.comment_count = infos.get("comment_count", 0)
        self.like_count = infos.get("like_count", 0)
        self.product_cover_img = infos.get("product_cover_img", "")
        self.eval_num = infos.get("eval_num", 0)
        self.product_create_time = infos.get("product_create_time", "")
        self.product_modified_time = infos.get("product_modified_time", "")
        self.product_price = infos.get("product_price", -1)
        self.star_level = infos.get("star_level", "")
        self.product_uname = infos.get("product_uname", "")
        self.product_uid = infos.get("product_uid", 0)
        self.islike = infos.get("islike", False)
        self.evaluation_count = infos.get("evaluation_count", 0)
        self.adjust_score = infos.get("adjust_score", 0)
        self.product_thumbnail = infos.get("product_thumbnail", [])

    def downloadImg(self):
        print "开始下载", self.product_name
        if len(self.product_cover_img) > 0:
            # downloadFile(self.product_cover_img, str(self.product_id))
            requestUrlContent(self.product_cover_img, os.path.join(self.img_cache_dir, str(self.product_id)))

        for i in self.product_thumbnail:
            # downloadFile(i, str(self.product_id))
            requestUrlContent(i, os.path.join(self.img_cache_dir, str(self.product_id)))

    def downloadHtml(self, db=None, mysqlDB=None):
        print "开始下载产品网页", self.product_name
        url = "http://store.baidu.com/product/view/%s.html"%str(self.product_id)
        cache_file_name = "%s.html"%str(self.product_id)
        requestUrlContent(url, self.html_cache_dir, cache_file_name)

        content = ""
        try:
            content = open(os.path.join(self.html_cache_dir, cache_file_name), 'rb').read()
        except Exception, e:
            print e

        product_intro = "" # 商品介绍

        # product intro
        try:
            product_intro_pattern = r'<div class=\"product-intro\">[\s\S]*?</div>'
            pattern = re.compile(product_intro_pattern)

            match = re.search(pattern, content)
            if match:
                product_intro = match.group()
                product_intro = unicode(product_intro, "utf-8")
                product_intro = product_intro[product_intro.index(">")+1:product_intro.rindex("</div>")]
        except Exception, e:
            print "get product intro error:", e
        
        product_detail = ""
        # product detail
        try:
            product_detail_pattern = r'<div class=\"product-detail\">[\s\S]*?</div>'
            pattern = re.compile(product_detail_pattern)

            match = re.search(pattern, content)
            if match:
                product_detail = match.group()
                product_detail = unicode(product_detail, "utf-8")
        except Exception, e:
            print "get product detail error:", e

        # 获取product thumbnails
        product_thumbnails = []
        try:
            product_thumbnails_pattern = r'<div class=\"wrap clearfix\">[\s\S]*?</div>'
            pattern = re.compile(product_thumbnails_pattern)

            match = re.search(pattern, content)
            if match:
                product_thumbnails_info = match.group()
                product_thumbnails_info = unicode(product_thumbnails_info, "utf-8")

                thumbnails_pattern = r'http\:\/\/[\s\S]*?\"'
                pattern = re.compile(thumbnails_pattern)
                match = re.findall(thumbnails_pattern, product_thumbnails_info)
                if match:
                    product_thumbnails = map(lambda x: x[:-1], match) 

        except Exception, e:
            print "get product thumbnails error:", e

        # buy url
        buy_url = ""
        try:
            buy_url_pattern = r'<div class=\"buy\">[\s\S]*?</div>'
            pattern = re.compile(buy_url_pattern)

            match = re.search(pattern, content)
            if match:
                buy_url_detail = match.group()
                buy_url_detail = unicode(buy_url_detail, "utf-8")

                http_pattern = r'http\:\/\/[\s\S]*?\"'
                pattern = re.compile(http_pattern)
                match = re.search(http_pattern, buy_url_detail)
                if match:
                    buy_url = match.group().strip()
        except Exception, e:
            print "get buy url error:", e

        if db:
            CREATE_PRODUCT_VIEW_TABLE = 'CREATE TABLE IF NOT EXISTS "products_view" ("product_id" INTEGER PRIMARY KEY  NOT NULL  UNIQUE, "product_intro" TEXT, "product_detail" TEXT, "product_thumbnails" TEXT, "buy_url" TEXT, "tags" TEXT )'
            try:
                db.execute(CREATE_PRODUCT_VIEW_TABLE)

                INSERT_COMMAND = "insert into products_view values (?,?,?,?,?,?)"
                _detail = self.product_title + " " + self.product_intro +" " +product_detail
                db.execute(INSERT_COMMAND, (self.product_id, product_intro, product_detail, str(product_thumbnails), buy_url, str(Tags.parserTags(_detail, mysqlDB, self.product_id))))
                db.commit()
            except Exception, e:
                print "insert product view error:", e

    def toTuple(self):
        return (
            self.product_id, 
            self.product_name, 
            self.product_title, 
            self.product_intro, 
            self.comment_count,
            self.like_count,
            self.product_cover_img,
            self.eval_num,
            self.product_create_time,
            self.product_modified_time,
            self.product_price,
            self.star_level,
            self.product_uname,
            self.product_uid,
            self.islike,
            self.evaluation_count,
            self.adjust_score,
            str(self.product_thumbnail))


if __name__ == "__main__":
    reload(sys)
    sys.setdefaultencoding('utf-8')
    db = sqlite3.connect("store.sqlite")
    p = ProductInfo({"product_id":2216})
    print p.downloadHtml(db)