#encoding=utf-8
from __future__ import unicode_literals

import os
import sys
import re
import sqlite3

"""

"""

class Evaluation:
    def _init(self):
        self.evaluationid = -1  # 测评报告id
        self.productid = -1     # 测评产品id
        self.userid = -1        # 测评人员id
        self.title = ""         # 测评报告的title
        self.score = 0          # 测评报告的评分
        self.content = ""       # 测评报告的全部内容
        self.thumbnail = ""     # 测评报告的缩略图
        self.excerpt = ""       # 测评报告的简要介绍

    def __init__(self, infos):
        cache_dir = os.path.join("cache", "evaluation")
        self.html_cache_dir = os.path.join(cache_dir, "html")
        if not os.path.isdir(self.html_cache_dir):
            os.makedirs(self.html_cache_dir)

        self.img_cache_dir = os.path.join(cache_dir, "img")
        if not os.path.isdir(self.img_cache_dir):
            os.makedirs(self.img_cache_dir)

        # infos is a dict
        if type(infos) != type({}):
            self._init()
            return

        self.evaluationid = infos.get("id", -1)
        self.productid = infos.get("product_id", -1)
        self.userid = infos.get("user_id", -1)
        self.title = infos.get("title", "")
        self.score = infos.get("score", -1)
        self.content = infos.get("content", "")
        self.thumbnail = infos.get("thumbnail", None)
        self.excerpt = infos.get("excerpt", "")

    def __str__(self):
        result = []
        result.append("Evalution Info:")
        result.append("  evaluation id: %s"%str(self.evaluationid))
        result.append("  product id: %s"%str(self.productid))
        result.append("  user id: %s"%str(self.userid))
        result.append("  title: %s"%str(self.title))
        result.append("  score: %s"%str(self.score))
        # result.append("  content: %s"%str(self.content))
        result.append("  thumbnail: %s"%str(self.thumbnail))
        result.append("  excerpt: %s"%str(self.excerpt))
        result.append("  product thumbnail: %s"%str(self.thumbnail))

        return "\n".join(result)

    def toTuple(self):
        return (
            self.evaluationid, 
            self.productid, 
            self.userid, 
            self.title, 
            self.score, 
            self.content, 
            self.thumbnail, 
            self.excerpt)


if __name__ == "__main__":
    evaluation = Evaluation({})
    print evaluation