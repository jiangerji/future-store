#encoding=utf-8
from __future__ import unicode_literals
import json
import sys
import sqlite3
import os
import httplib
import time


"""
pn: 获取页数
limit: 每页的数量
_: 当前的时间
"""
BASE_URL_FORMAT = "http://store.baidu.com/news/api/list?pn=1&limit=10&_=1415932708709"

class NewsInfo:

    def __init__(self, infos):
        self.id = infos.get("id", 0)
        self.create_time = infos.get("create_time", "")
        self.title = infos.get("title", 0)
        self.excerpt = infos.get("excerpt", 0)
        self.status = infos.get("status", 0)
        self.comment_status = infos.get("comment_status", 0)
        self.thumbnails = infos.get("thumbnails", 0)
        self.source = infos.get("source", 0)
        self.cat_id = infos.get("cat_id", 0)
        self.comment_count = infos.get("comment_count", 0)
        self.like_count = infos.get("like_count", 0)
        self.weights = infos.get("weights", 0)

    def __str__(self):
        result = []
        result.append("News Info:")
        result.append("  news id: %s"%str(self.id))
        result.append("  new title: %s"%str(self.title))
        result.append("  new excerpt: %s"%str(self.excerpt))
        result.append("  create_time: %s"%str(self.create_time))
        result.append("  status: %s"%str(self.status))
        result.append("  comment_status: %s"%str(self.comment_status))
        result.append("  thumbnails: %s"%str(self.thumbnails))
        result.append("  source: %s"%str(self.source))
        result.append("  cat_id: %s"%str(self.cat_id))
        result.append("  comment_count: %s"%str(self.comment_count))
        result.append("  like_count: %s"%str(self.like_count))
        result.append("  weights: %s"%str(self.weights))

        return "\n".join(result)

    def get_id(self):
        return self.id

    def toTuple(self):
        return (
            self.id, 
            self.create_time,
            self.title, 
            self.excerpt, 
            self.status,
            self.comment_status,
            self.thumbnails,
            self.source,
            self.cat_id,
            self.comment_count,
            self.like_count,
            self.weights)

    def downloadImg(self):
        # 下载thumbnail

        # 下载网页

        # 下载网页中的
        pass

def parseNewsList(content):
    global index

    result = []

    all = json.loads(content)
    error_code = all.get("error_code")
    error_msg = all.get("error_msg")
    if error_code == 0:
        # 获取成功
        data = all.get("data")
        news_list = data.get("list")
        for news in news_list:
            news_info = NewsInfo(news)
            result.append(news_info)
    else:
        # 获取失败
        print "获取新闻列表失败，", error_msg

    return result

from utils import *
import re

def _get_product_buy_info(content):
    #     content = '<div class="product-side fl-left">\
    # <div class="buy"><a href="          http://item.jd.com/1059164.html\
    #           " class="active" onclick="_hmt.push([\'_trackEvent\', \'buy\', \'click\', \'倍轻松眼部按摩器 isee4\']);" target="_blank">去购买</a></div>\
    # <div class="phone-type clearfix">\
    # <div class="fl-left">支持机型：</div>\
    # <div class="items">无</div>'

    buy_url_pattern = r'<div class=\"buy\">[\s\S]*?</div>'
    pattern = re.compile(buy_url_pattern)

    buy_url = ""
    match = re.search(pattern, content)
    if match:
        buy_url = match.group()
        start_index = buy_url.index("<a") + 2
        start_index = buy_url.index("href=", start_index) + len("href=")
        start_index = buy_url.index('"', start_index)+1
        end_index = buy_url.index('"', start_index)
        buy_url = buy_url[start_index: end_index].strip()

    return buy_url

def get_news_content(news_id):
    # http://store.baidu.com/news/3671.html
    url = "http://store.baidu.com/news/%s.html"%news_id
    requestUrlContent(url, "cache"+os.path.sep+"html", "%s.html"%news_id)

    content = open("cache"+os.path.sep+"html"+os.path.sep+"%s.html"%news_id, 'rb').read()
    # 获取summary
    summary_pattern = r'<div class=\"d-summary\">[\s\S]*?</div>'
    pattern = re.compile(summary_pattern)

    summary = ""
    match = re.search(pattern, content)
    if match:
        summary = match.group()
        summary = unicode(summary, "utf-8")
        # print summary, summary.rindex("<")
        summary = summary[summary.index(">")+1:summary.rindex("</div>")]
        # print summary

    # 获取content
    content_pattern = r'<div class="d-artical-content" id="sourceContent">[\s\S]*?</div>'
    pattern = re.compile(content_pattern)

    html_content = ""
    match = re.search(pattern, content)
    if match:
        html_content += match.group()

    buy_url = ""
    try:
        buy_url = _get_product_buy_info(content)
    except Exception, e:
        print "get product buy info exception:", e

    return summary, html_content, buy_url


def news_spider():
    quota = 100

    db = sqlite3.connect("store.sqlite")
    db.text_factory = lambda x: unicode(x, 'utf-8', 'ignore')

    try:
        CREATE_COMMAND = 'CREATE  TABLE  IF NOT EXISTS "news" ("id" INTEGER PRIMARY KEY  NOT NULL  UNIQUE , "create_time" TEXT, "title" TEXT, "excerpt" TEXT, "status" INTEGER, "comment_status" INTEGER, "thumbnails" TEXT, "source" TEXT, "cat_id" INTEGER, "comment_count" INTEGER, "like_count" INTEGER, "weights" INTEGER)'
        db.execute(CREATE_COMMAND)

        CREATE_NEWS_CONTENT_TABEL = 'CREATE TABLE IF NOT EXISTS "news_content" ("id" INTEGER PRIMARY KEY  NOT NULL  UNIQUE, "summary" TEXT, "content" TEXT, "store_url" TEXT)'
        db.execute(CREATE_NEWS_CONTENT_TABEL)

        INSERT_COMMAND = "insert into news values (?,?,?,?,?,?,?,?,?,?,?,?)"
        INSERT_NEWS_CONTENT_COMMAND = "insert into news_content values (?,?,?,?)"

        index = 1
        url_format = "http://store.baidu.com/news/api/list?pn=%%d&limit=%d&_=%%s"%quota
        while True:
            url = url_format%(index, str(int(time.time()*100)))

            try:
                news_list = parseNewsList(requestUrlContent(url))

                for news in news_list:
                    try:
                        db.execute(INSERT_COMMAND, news.toTuple())
                    except Exception, e:
                        print "insert product info exception:", e

                    print "get news content", news.get_id()
                    summary, news_content, buy_url = get_news_content(news.get_id())

                    time.sleep(0.1)
                    # print news_content
                    db.execute(INSERT_NEWS_CONTENT_COMMAND, (news.get_id(), summary, news_content, buy_url))
                    # print "insert new content"

                print "handle", len(news_list)
                if len(news_list) < quota:
                    break
            except Exception, e:
                print "Handle", url, "exception", e

            index += 1
            db.commit()
            time.sleep(1)

    except Exception, e:
        print e

    db.commit()
    db.close()

def re_test(news_id):
    import re
    # news_id = 1
    # 将正则表达式编译成Pattern对象
    content_pattern = r'<div class=\"d-summary\">[\s\S]*?</div>'
    # content_pattern = r'<div.*>[\s\S]*?</div>'
    pattern = re.compile(content_pattern)
     
    # 使用Pattern匹配文本，获得匹配结果，无法匹配时将返回None
    content = 'asd<div class="d-summary">sdsd\nfadf中国</div>\nfasdf'
    # content = open(".cache"+os.path.sep+"html"+os.path.sep+"%d.html"%news_id).read()
    # print content
    # # return

    match = re.search(pattern, content)
    if match:
        print match.group()

    # return

    # match = pattern.match(content)


    # if match:
    #     # 使用Match获得分组信息·
    #     print match.group()
    # return

    content_pattern = r'<div class="d-artical-content" id="sourceContent">[\s\S]*?</div>'

    content1 = '<div class="d-artical-content" id="sourceContent">\
<p>&nbsp; 11.10~11.14 热门单品汇总！这是特别的一周，举世瞩目的APEC大会在京城召开，也让我们体验到了&ldquo;APEC蓝&rdquo;魅力，还见证了大帝都的交通也是可以如此通畅。这周，注定是不平凡的一周：Nixie自拍飞行器成了自拍达人微博、朋友圈热门分享的神器；Withings Activite智能手表，成了最&ldquo;手表&rdquo;的智能手表，收到众多青睐；B4RM4N智能调酒杯让单身宅男也能一秒变身夜店里受人瞩目的焦点；SKULLY智能摩托车头盔，让热爱机车的人们再一次狂热起来；Fireside智能电子相框 让人们发现这个被遗忘的相框还能这样智能化.....</p></div>'

    content = open(".cache"+os.path.sep+"html"+os.path.sep+"%d.html"%news_id).read()
    # print content
    print content.find('<div class="d-artical-content" id="sourceContent">')
    
    pattern = re.compile(content_pattern, re.I | re.M)

    match = re.search(pattern, content)

    # content = '<div class="d-artical-content" id="sourceContent">\n<p>fasf</div>'
    # match = pattern.match(content)
    if match:
        print match.group()
     
    ### 输出 ###
    # hello

if __name__ == "__main__":
    reload(sys)
    sys.setdefaultencoding('utf-8')
    news_spider()
    # _get_product_buy_info("")




