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

import NewsSpider
import utils

_FAKE = True

# 创建news table
CREATE_COMMAND = 'CREATE  TABLE  IF NOT EXISTS "news" ("id" INTEGER PRIMARY KEY  NOT NULL  UNIQUE , "create_time" TEXT, "title" TEXT, "excerpt" TEXT, "status" INTEGER, "comment_status" INTEGER, "thumbnails" TEXT, "source" TEXT, "cat_id" INTEGER, "comment_count" INTEGER, "like_count" INTEGER, "weights" INTEGER)'

# 创建news content table
CREATE_NEWS_CONTENT_TABEL = 'CREATE TABLE IF NOT EXISTS "news_content" ("id" INTEGER PRIMARY KEY  NOT NULL  UNIQUE, "summary" TEXT, "content" TEXT, "store_url" TEXT)'

INSERT_COMMAND = "insert into news values (?,?,?,?,?,?,?,?,?,?,?,?)"
INSERT_NEWS_CONTENT_COMMAND = "insert into news_content values (?,?,?,?)"

def get_news_list(index, quota=100):
    if index < 1:
        return []

    url_format = "http://store.baidu.com/news/api/list?pn=%%d&limit=%d&_=%%s"%quota

    url = url_format%(index, str(int(time.time()*100)))
    content = utils.requestUrlContent(url)
    news_list = NewsSpider.parseNewsList(content)
    return news_list

# 将sqliteName中的数据都插入到网站数据中
def insert_articles_main(quota=1, ignore=-1, sqliteName=None):
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

    if mysqlConn == None or mysqlCur == None:
        # 打开数据失败，
        return (False, "Open mysql database error!")
    
    if sqliteName is None:
        # news更新数据库不存在，不进行更新操作
        return (False, "update sqlite is not existes!")

    allNews = None
    sqliteDB = None

    try:
        sqliteDB = sqlite3.connect(sqliteName)
        allNews = sqliteDB.execute('select id, title, excerpt, thumbnails from news').fetchall()
    except Exception, e:
        return (False, "get update news from database error:"+str(e))

    count = 0
    ignore_count = 0

    # 开始向网站database插入数据
    for news in allNews:
        ignore_count += 1
        if ignore_count <= ignore:
            continue

        _id, title, introtext, thumbnails = news
        print "\n================start to insert news================"
        print "insert news", _id, title, introtext, thumbnails

        # 下载图标
        # images是 erji_tz_portfolio_xref_content需要
        images = utils.downloadNewsThumbnails(_id, thumbnails)
        # print "insert images", images
        if images == None:
            print "download", thumbnails, "failed!"
            continue

        # 插入asset表
        asset_id = utils.insertIntoAssets(mysqlCur, title)

        # 获取full text
        full_text = sqliteDB.execute('select content from news_content where id='+str(_id)).fetchone()[0]
        # 插入到内容表里面
        content_id = utils.insertIntoContent(mysqlCur, asset_id, title, introtext, full_text)

        if content_id <= 0:
            print "插入内容表失败"
            continue

        # 插入应用图片
        utils.insert_xref_content(mysqlCur, content_id, images)

        count += 1
        if count >= quota:
            break

    sqliteDB.close()

    try:
        mysqlConn.commit()
        mysqlConn.close()
    except MySQLdb.Error,e:
         print "Mysql Error %d: %s" % (e.args[0], e.args[1])

    return (True, "Total insert %d news!"%count)

"""
quota: 表示此次需要更新的新闻数量的上限
"""
def update(quota=1):
    updateDatabaseName = "update.news.sqlite"

    db = sqlite3.connect("store.sqlite")
    db.text_factory = lambda x: unicode(x, 'utf-8', 'ignore')

    updateDB = sqlite3.connect(updateDatabaseName)
    updateDB.text_factory = lambda x: unicode(x, 'utf-8', 'ignore')

    dbExecState = True
    try:
        db.execute(CREATE_COMMAND)
        db.execute(CREATE_NEWS_CONTENT_TABEL)
        updateDB.execute(CREATE_COMMAND)
        updateDB.execute(CREATE_NEWS_CONTENT_TABEL)
    except Exception, e:
        dbExecState = False
        print e # 创建表失败，不用继续操作了
        return

    index = 1
    succ_count = 0
    finished = False
    while True:
        news_list = get_news_list(index)

        for news in news_list:
            try:
                db.execute(INSERT_COMMAND, news.toTuple())

                # 插入db成功，表示这是新的news，否则会走到异常处理流程
                updateDB.execute(INSERT_COMMAND, news.toTuple())

                summary, news_content, buy_url = NewsSpider.get_news_content(news.get_id())

                db.execute(INSERT_NEWS_CONTENT_COMMAND, (news.get_id(), summary, news_content, buy_url))
                updateDB.execute(INSERT_NEWS_CONTENT_COMMAND, (news.get_id(), summary, news_content, buy_url))
                
                print "insert news", news.get_id(), news.getTitle(), summary, buy_url, "\n"
                succ_count += 1
            except Exception, e:
                print news.get_id(), news.getTitle(), "is already existes!\n"

            if succ_count >= quota:
                finished = True
                break

        if finished:
            break

        index += 1

        db.commit()
        updateDB.commit()

    db.commit()
    updateDB.commit()

    db.close()
    updateDB.close()

    # 将uypdateDB中的数据插入到网站数据中
    print insert_articles_main(quota, -1, updateDatabaseName)
    try:
        os.remove(updateDatabaseName)
    except Exception, e:
        print e


if __name__ == "__main__":
    reload(sys)
    sys.setdefaultencoding('utf-8')

    workDir = os.path.dirname(os.path.realpath(sys.argv[0]))
    os.chdir(workDir)

    logFile = utils.openLogFile()

    oldStdout = sys.stdout  
    sys.stdout = logFile

    print "change work direcotory to", workDir

    count = 1
    ignore = -1

    if ("--fake" in sys.argv):
        _FAKE = True

    if len(sys.argv) > 1:
        count = abs(int(sys.argv[1]))


    if len(sys.argv) > 2:
        ignore = int(sys.argv[2])

    print "============================================"
    print "start update news:", time.asctime(), count

    update(count)

    logFile.close()  
    if oldStdout:  
        sys.stdout = oldStdout





