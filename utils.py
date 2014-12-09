#encoding=utf-8
from __future__ import unicode_literals
import sys
import os
import hashlib
import sqlite3
import time
import Image
import codecs
import random

MYSQL_PASSPORT = "debian-sys-maint"
MYSQL_PASSWORD = "eMBWzH5SIFJw5I4c"
MYSQL_DATABASE = "future-store"

def md5(source):
    result = hashlib.md5(source.encode('utf-8')).hexdigest()
    return result
PIC_SUFFIX = ["png", "jpg", "gif", "jpeg", "bmp"]
def requestUrlContent(url, cache_dir="cache", filename=None):
    if not os.path.isdir(cache_dir):
        os.makedirs(cache_dir)

    ext = os.path.splitext(url)[-1]
    if filename == None:
        filename = md5(url) + ext

    target_path = os.path.join(".", cache_dir)
    target_path = os.path.join(target_path, filename)
    command = 'wget "%s" -O %s '%(url, target_path)
    # print command, type(command), type(command.decode("utf-8"))
    print command
    # command = 'wget "http://bs.baidu.com/dulife/100500mf6hfqfozfnnhqph_副本.jpg" -O .\\cache\\news\\img\\1.png'
    if not os.path.isfile(target_path):
        state = os.system(command.encode("utf-8")) # 在windows下是gb2312, 在ubuntu主机上应该是utf-8
        # print state
    else:
        print target_path, "is already downloaded!"

    # if url.lower().endswith(".png") or url.lower().endswith('.jpg') or url.lower().endswith('.gif') or url.lower().endswith("jpeg"):
    if ext[1:].lower() in PIC_SUFFIX:
        return target_path

    return open(target_path).read()


# 下载news的缩略图，并插入到数据库中
def downloadNewsThumbnail():
    db = sqlite3.connect("store.sqlite")
    cursor = db.execute("SELECT id, thumbnails FROM news")
    for i in cursor.fetchall():
        _id, url = i
        requestUrlContent(url, "cache"+os.path.sep+"news"+os.path.sep+"img"+os.path.sep+str(_id), os.path.basename(url))
        raw_input()

import MySQLdb
ASSETS_LFT = 151
ASSETS_RGT = 152
ASSETS_RULES = '{"core.delete":{"6":1},"core.edit":{"6":1,"4":1},"core.edit.state":{"6":1,"5":1}}'
def insertIntoAssets(cursor, title):
    # insert value into assets table, first step, return the id to insert content table
    global ASSETS_LFT, ASSETS_RGT
    cursor.execute('select lft, rgt, name from erji_assets where name like "com_content.article%" order by `id` desc limit 0, 1')
    _lft, _rgt, _name_id = cursor.fetchone()
    _lft += 2
    _lft = max(_lft, ASSETS_LFT)
    _rgt += 2
    _rgt = max(_rgt, ASSETS_RGT)
    name_id = int(_name_id.split(".")[-1]) + 1

    INSERT_ASSETS = 'insert into erji_assets (parent_id, lft, rgt, level, name, title, rules) values (%s,%s,%s,%s,%s,%s,%s)'
    assets_name = "com_content.article.%d"%(name_id)
    assets_values = [36, _lft, _rgt, 3, assets_name, title, ASSETS_RULES]
    a = cursor.execute(INSERT_ASSETS, assets_values)

    ASSETS_LFT += 2
    ASSETS_RGT += 2

    print "inset asset", cursor.lastrowid
    return cursor.lastrowid


#/**********************************************************/
CONTENT_ATTRIBS = '{"show_title":"","link_titles":"","show_intro":"","show_category":"","link_category":"","show_parent_category":"","link_parent_category":"","show_author":"","link_author":"","show_create_date":"","show_modify_date":"","show_publish_date":"","show_item_navigation":"","show_icons":"","show_print_icon":"","show_email_icon":"","show_vote":"","show_hits":"","show_noauth":"","urls_position":"","alternative_readmore":"","article_layout":"","show_related_article":"","show_related_heading":"","related_heading":"","show_related_type":"","show_related_featured":"","related_image_size":"","related_orderby":"","show_publishing_options":"","show_article_options":"","show_urls_images_backend":"","show_urls_images_frontend":"","tz_portfolio_redirect":"","show_attachments":"","show_image":"","tz_use_image_hover":"","tz_image_timeout":"","portfolio_image_size":"","portfolio_image_featured_size":"","detail_article_image_size":"","show_image_gallery":"","detail_article_image_gallery_size":"","image_gallery_slideshow":"","show_arrows_image_gallery":"","show_controlNav_image_gallery":"","image_gallery_pausePlay":"","image_gallery_pauseOnAction":"","image_gallery_pauseOnHover":"","image_gallery_useCSS":"","image_gallery_slide_direction":"","image_gallery_animation":"","image_gallery_animSpeed":"","image_gallery_animation_duration":"","show_video":"","video_width":"","video_height":"","tz_show_gmap":"","tz_gmap_width":"","tz_gmap_height":"","tz_gmap_mousewheel_zoom":"","tz_gmap_zoomlevel":"","tz_gmap_latitude":"","tz_gmap_longitude":"","tz_gmap_address":"","tz_gmap_custom_tooltip":"","useCloudZoom":"","article_image_zoom_size":"","zoomWidth":"","zoomHeight":"","position":"","adjustX":"","adjustY":"","tint":"","tintOpacity":"","lensOpacity":"","softFocus":"","smoothMove":"","showTitle":"","titleOpacity":"","show_comment":"","tz_comment_type":"","tz_show_count_comment":"","disqusSubDomain":"","disqusApiSecretKey":"","disqusDevMode":"","show_twitter_button":"","show_facebook_button":"","show_google_button":"","show_extra_fields":"","field_show_type":""}'

CONTENT_INSERT_COMMAND = 'insert into erji_content (asset_id, title, alias, introtext, `fulltext`, state, catid, created, created_by, created_by_alias, modified, modified_by, checked_out, checked_out_time, publish_up, publish_down, images, urls, attribs, version, ordering, metakey, metadesc, access, hits, metadata, featured, language, xreference) values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)'

CREATED_OWNER = None
_OWNERS = None

def insertIntoContent(cursor, _asset_id, _title, _introtext, _fulltext, _catid=8):
    """
    _asset_id: 由insertIntoAssets返回的值
    _title: 文章的标题
    _introtext: 文章的简要介绍
    _fulltext: 文章全部内容
    """
    global CREATED_OWNER, _OWNERS
    if _OWNERS == None:
        # cursor.execute('select id from erji_users where username="jiangerji"')
        # CREATED_OWNER = cursor.fetchone()[0]

        cursor.execute('select id from erji_users')
        _OWNERS = map(lambda x: x[0],  cursor.fetchall())
    CREATED_OWNER = random.choice(_OWNERS)

    asset_id = _asset_id
    title = _title
    alias = title
    introtext = _introtext
    fulltext = _fulltext
    state = 1
    catid = _catid
    created = time.strftime("%Y-%m-%d %H:%M:%S")
    created_by = CREATED_OWNER
    created_by_alias = ""
    modified = time.strftime("%Y-%m-%d %H:%M:%S")
    modified_by = CREATED_OWNER
    checked_out = CREATED_OWNER
    checked_out_time = time.strftime("%Y-%m-%d %H:%M:%S")
    publish_up = "0000-00-00 00:00:00"
    publish_down = "0000-00-00 00:00:00"
    images = ""
    urls = ""
    attribs = CONTENT_ATTRIBS
    version = 1
    ordering = 0
    metakey = '可穿戴,可穿戴设备,百度可穿戴设备,百度可穿戴,智能设备,智能可穿戴设备,超智能设备,百度智能设备,便携设备,便携智能设备,百度便携设备, 人体设备,智能人体设备,百度人体设备,便携人体设备,dulife,dulife平台,奇酷网,奇酷,360奇酷,小米酷玩,小米酷玩频道,百度硬件,智能硬件,硬件,智能移动设备,智能移动硬件,移动设备,移动硬件,可穿戴硬件,点名时间,母亲节'
    metadesc = ''
    access = 1
    hits = 1
    metadata = '{"robots":"","author":"","rights":"","xreference":""}'
    featured = 0
    language = "*"
    xreference = ""

    values = (asset_id, title, alias, introtext, fulltext, state, catid, created, created_by, created_by_alias, modified, modified_by, checked_out, checked_out_time, publish_up, publish_down, images, urls, attribs, version, ordering, metakey, metadesc, access, hits, metadata, featured, language, xreference)

    count = cursor.execute(CONTENT_INSERT_COMMAND, values)

    if count > 0:
        return cursor.lastrowid
    else:
        return count

WWW_ROOT = "/home/ubuntu/drupal/dreame-mall"

import platform
if platform.system() == 'Windows':
    WWW_ROOT = ""

_TARGET_CACHE_DIR = "media"+os.path.sep+"tz_portfolio"+os.path.sep+"article"+os.path.sep+"cache"
TARGET_CACHE_DIR = os.path.join(WWW_ROOT, _TARGET_CACHE_DIR)
def downloadNewsThumbnails(_id, url):
    if not os.path.isdir(TARGET_CACHE_DIR):
        os.makedirs(TARGET_CACHE_DIR)

    cache_dir = "cache" + os.path.sep + "news" + os.path.sep + "img" + os.path.sep + str(_id)
    thumbnails_path = requestUrlContent(url, cache_dir, md5(url) + os.path.splitext(url)[-1])

    if not os.path.isfile(thumbnails_path):
        return None

    print "处理thumbnails", thumbnails_path
    print "targat", TARGET_CACHE_DIR
    # 处理成5种尺寸, 按宽度自适应
    # XS:100, S:200, M:400, L:600, XL:900
    im = Image.open(thumbnails_path)
    width, height = im.size
    filename, ext = os.path.splitext(os.path.basename(thumbnails_path))

    # XS
    _width = 100
    _heigh = _width * height / width
    target_file = os.path.join(TARGET_CACHE_DIR, filename+"_portfolio_"+"XS"+ext)
    out = im.resize((_width, _heigh), Image.ANTIALIAS)
    out.save(target_file)

    # S
    _width = 200
    _heigh = _width * height / width
    target_file = os.path.join(TARGET_CACHE_DIR, filename+"_portfolio_"+"S"+ext)
    out = im.resize((_width, _heigh), Image.ANTIALIAS)
    out.save(target_file)

    # M
    _width = 400
    _heigh = _width * height / width
    target_file = os.path.join(TARGET_CACHE_DIR, filename+"_portfolio_"+"M"+ext)
    out = im.resize((_width, _heigh), Image.ANTIALIAS)
    out.save(target_file)

    # L
    _width = 600
    _heigh = _width * height / width
    target_file = os.path.join(TARGET_CACHE_DIR, filename+"_portfolio_"+"L"+ext)
    out = im.resize((_width, _heigh), Image.ANTIALIAS)
    out.save(target_file)

    # XL
    _width = 900
    _heigh = _width * height / width
    target_file = os.path.join(TARGET_CACHE_DIR, filename+"_portfolio_"+"XL"+ext)
    out = im.resize((_width, _heigh), Image.ANTIALIAS)
    out.save(target_file)

    return os.path.join(_TARGET_CACHE_DIR, filename+"_portfolio"+ext)

# 插入到xref content table中
XREF_INSERT_COMMAND = 'insert into erji_tz_portfolio_xref_content (contentid, groupid, images, images_hover, gallery, video, type, imagetitle, gallerytitle, videotitle, videothumb, attachfiles, attachtitle, attachold, audio, audiothumb, audiotitle, quote_author, quote_text, link_url, link_title, link_attribs) values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)'
def insert_xref_content(cursor, _contentid, _images):
    contentid = _contentid
    groupid = 0
    images = _images
    images_hover = ""
    gallery = ""
    video = ""
    content_type = "image"
    imagetitle = ""
    gallerytitle = ""
    videotitle = ""
    videothumb = ""
    attachfiles = ""
    attachtitle = ""
    attachold = ""
    audio = ""
    audiothumb = ""
    audiotitle = ""
    quote_author = ""
    quote_text = ""
    link_url = ""
    link_title = ""
    link_attribs = '{"link_target":"_blank","link_follow":"nofollow"}'

    values = (contentid, groupid, images, images_hover, gallery, video, content_type, imagetitle, gallerytitle, videotitle, videothumb, attachfiles, attachtitle, attachold, audio, audiothumb, audiotitle, quote_author, quote_text, link_url, link_title, link_attribs)
    return cursor.execute(XREF_INSERT_COMMAND, values)

def insertArtical(cursor, quota=1, ignore=-1, sqliteName=None):
    _sqliteName = "store.sqlite"
    if sqliteName != None:
        _sqliteName = sqliteName

    db = sqlite3.connect(_sqliteName)
    allNews = db.execute('select id, title, excerpt, thumbnails from news').fetchall()

    count = 0
    ignore_count = 0

    for news in allNews:
        ignore_count += 1
        if ignore_count <= ignore:
            continue

        _id, title, introtext, thumbnails = news
        # print _id, title, introtext, thumbnails
        # images是 erji_tz_portfolio_xref_content需要
        images = downloadNewsThumbnails(_id, thumbnails)
        print "insert images", images
        if images == None:
            print "下载", thumbnails, "失败！"
            continue

        asset_id = insertIntoAssets(cursor, title)


        # 获取full text
        full_text = db.execute('select content from news_content where id='+str(_id)).fetchone()[0]
        content_id = insertIntoContent(cursor, asset_id, title, introtext, full_text)

        if content_id <= 0:
            continue

        insert_xref_content(cursor, content_id, images)

        count += 1
        if count >= quota:
            break

def insert_article_main(quota=1, ignore=-1, sqliteName=None):
    
    try:
        conn=MySQLdb.connect(host="localhost",user="debian-sys-maint",passwd="eMBWzH5SIFJw5I4c",db="future-store",charset="utf8")
        cur=conn.cursor()

        insertArtical(cur, quota, ignore, sqliteName)

        cur.close()
        conn.commit()
        conn.close()
    except MySQLdb.Error,e:
         print "Mysql Error %d: %s" % (e.args[0], e.args[1])
"""
在log目录下创建filename.创建日期.log的日志文件
如果为None, filename默认为调用该接口的python文件名
"""
def openLogFile(filename=None):
    if filename == None:
        filename = os.path.splitext(os.path.basename(sys.argv[0]))[0]

    currentDate = time.strftime("%Y-%m-%d",time.localtime()) 

    filename += "-" + currentDate + ".log"

    logDir = "log"
    if not os.path.isdir(logDir):
        os.makedirs(logDir)

    return codecs.open("log"+os.path.sep+filename, "a+", "utf-8")

if __name__ == "__main__":
    reload(sys)
    sys.setdefaultencoding('utf-8')
    # requestUrlContent("http://store.baidu.com/product/api/recommendList?cat_id=0&orderBy=hot&order=desc&pn=1&limit=36")
    # downloadNewsThumbnail()
    # insert_article_main()
    count = 1
    ignore = -1

    if len(sys.argv) > 1:
        count = abs(int(sys.argv[1]))


    if len(sys.argv) > 2:
        ignore = int(sys.argv[2])

    # insert_article_main(count, ignore)
    openLogFile()
