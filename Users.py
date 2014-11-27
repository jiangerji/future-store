#encoding=utf-8
from __future__ import unicode_literals
import sys
import os
import hashlib
import sqlite3
import time
import platform
import MySQLdb
import random

_FAKE = False

def fake_articel_author(quota=1, ignore=-1):
    try:
        conn = None
        if platform.system() == 'Windows':
            conn=MySQLdb.connect(host="localhost",user="root", passwd="123456",db="world",charset="utf8")
        else:
            conn=MySQLdb.connect(host="localhost",user="debian-sys-maint",passwd="eMBWzH5SIFJw5I4c",db="future-store",charset="utf8")
        cur=conn.cursor()

        # 获取目前所有用户ID
        cur.execute('select id from erji_users')
        users = map(lambda x: x[0],  cur.fetchall())
        users_count = len(users)

        # 获取所有category为8的文章，修改他们的author
        cur.execute('select id from erji_content where catid=8')
        for content in cur.fetchall():
            _id = content[0]
            created_by = users[random.randint(0, users_count-1)]

            print _id, created_by
            cur.execute('update erji_content set `created_by`=%s, modified_by=%s where id=%s', (created_by, created_by, _id))

        cur.close()
        conn.commit()
        conn.close()
    except MySQLdb.Error,e:
         print "Mysql Error %d: %s" % (e.args[0], e.args[1])

if __name__ == "__main__":
    reload(sys)
    sys.setdefaultencoding('utf-8')

    import codecs

    logFile = codecs.open("users.log", "w", "utf-8")

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

    fake_articel_author(count, ignore)

    logFile.close()  
    if oldStdout:  
        sys.stdout = oldStdout