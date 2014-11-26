#encoding=utf-8
from __future__ import unicode_literals
import sys
import os
import hashlib
import sqlite3
import time
import platform
import MySQLdb

"""
智能生活    10
    插座 开关 防丢 灯 窗帘 家电 家居 马桶 电饭煲 水杯 路由器 安防 监控 水壶 咖啡 耳机 眼镜 生活
    手环 电视 

运动娱乐    11
    耳机 眼镜 头盔 跑步机 xbox ps 无人 游戏 gopro 运动 娱乐 

健康医疗    12
    健康 医疗 血糖 血压 心跳 医生 心电 智能水壶 药 温度计 体重 

智能厨房    13
    厨房 煮 炒 煎 炸 蒸 咖啡 
"""

LIFE    = 10
SPORT   = 11
HEALTHY = 12
KITCHEN = 13
SECURITY= 14

KEYS = {
    LIFE: ["插座","开关","防丢","灯","窗帘","家电","家居","马桶","电饭煲","水杯","路由","安防","监控","水壶","咖啡","耳机","眼镜","生活","手环","电视","手表","腕表","手镯","报警","节能","家中","手腕","遥控器","POS机","净化","打印机","移动电源","名片","戒指","沐浴","加湿器","电动车","牙刷","充电"],

    SPORT: ["耳机","眼镜","头盔","跑步机","xbox","ps","无人","游戏","gopro","运动","娱乐","视频","音乐","高清","手表","腕表","手镯","手环","手势","遥控器","玩耍","相机","影像","光圈","盒子","戒指","飞行","摄像机","相框","意念","绘画","跳舞","机器人","充电宝","气压","光学技术","手机壳","充电"],

    HEALTHY: ["健康","医疗","血糖","血压","心跳","医生","心电","智能水壶","药","温度计","体重","睡眠","净化","肌肤","体温","婴儿","口罩","流感","病毒","加湿器","牙刷","监护器"],

    KITCHEN: ["厨房","煮","炒","煎","炸","蒸","咖啡"],

    SECURITY: ["监控","安防","报警","警报","监视","隐私","求救","SOS"]
}

NAMES = {
    LIFE : u"智能生活",
    SPORT: u"运动娱乐",
    HEALTHY: u"健康医疗",
    KITCHEN: u"智能厨房",
    SECURITY: u"智能安全"
}

def mark_tags_to_products(quota=1, ignore=-1):
    try:
        conn = None
        if platform.system() == 'Windows':
            conn=MySQLdb.connect(host="localhost",user="root", passwd="123456",db="world",charset="utf8")
        else:
            conn=MySQLdb.connect(host="localhost",user="debian-sys-maint",passwd="eMBWzH5SIFJw5I4c",db="future-store",charset="utf8")
        cur=conn.cursor()

        _mark_tags_to_products(cur, quota, ignore)

        cur.close()
        conn.commit()
        conn.close()
    except MySQLdb.Error,e:
         print "Mysql Error %d: %s" % (e.args[0], e.args[1])

def _mark_tags_to_products(cursor, quota=1, ignore=-1):
    # db = sqlite3.connect("store.sqlite")
    # allProducts = db.execute('select product_id, product_intro, product_detail from products_view').fetchall()
    cursor.execute('select id, title, introtext, `fulltext` from erji_content where catid=14')
    allProducts = cursor.fetchall()

    count = 0
    ignore_count = 0

    for product in allProducts:
        ignore_count += 1
        if ignore_count <= ignore:
            continue

        product_id, product_title, product_intro, product_detail = product
        # product_title = db.execute('select product_title from products_info where product_id='+str(product_id)).fetchone()[0]
        detail = product_title + " " +product_intro + " " + product_detail
        
        tags = []
        for key in KEYS.keys():
            for value in KEYS[key]:
                if detail.find(value) >= 0:
                    # tags.append(NAMES[key])
                    tags.append(key)
                    break

        if len(tags) == 0:
            # tags.append(NAMES[LIFE])
            tags.append(LIFE)

        # print product_id, product_intro, str(tags).encode("gb2312")
        print "============="
        # db.execute('update products_view set tags=? where product_id=?', (",".join(tags), product_id))

        values = map(lambda x: (x, product_id), tags)
        print values
        cursor.executemany('insert into erji_tz_portfolio_tags_xref (tagsid, contentid) values (%s,%s)', values)
        count += 1
        if count >= quota:
            break

    # db.commit()
    # db.close()



if __name__ == "__main__":
    reload(sys)
    sys.setdefaultencoding('utf-8')

    import codecs

    logFile = codecs.open("tags.log", "w", "utf-8")

    oldStdout = sys.stdout  
    sys.stdout = logFile

    count = 1
    ignore = -1

    if len(sys.argv) > 1:
        count = abs(int(sys.argv[1]))


    if len(sys.argv) > 2:
        ignore = int(sys.argv[2])

    mark_tags_to_products(count, ignore)

    logFile.close()  
    if oldStdout:  
        sys.stdout = oldStdout