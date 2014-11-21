#encoding=utf-8
import hashlib

def md5(source):
    result = hashlib.md5(source.encode('utf-8')).hexdigest()
    return result

def filename_generator(target_url):
    return md5(target_url)

class DownloadTask:

    """
    target_url: 下载地址
    filename: 下载后保存的名字
    directory: 下载保存的目录位置
    """
    def __init__(self, target_url, filename, directory):
        self.target_url = target_url
        self.filename = filename
        self.directory = directory

    def start(self, download_manager):
        # 启动线程下载，下载结束后，通过downloadManager回调
        pass

class DownloadManager:

    def __init__(self):
        pass

    def addTask(self):
        pass

    def taskFinishCallback(self, download_task):
        pass

import os
def downloadFile(target_url, directory, filename=None):
    if filename == None:
        filename = filename_generator(target_url)

    output_path = os.path.join("."+os.path.sep+"img", directory)
    if not os.path.isdir(output_path):
        os.makedirs(output_path)
    output_path = os.path.join(output_path, filename)
    command = "wget -O %s %s"%(output_path, target_url)
    # print command
    os.system(command)
    print "  下载", target_url, "到", output_path

if __name__ == "__main__":
    target_url = "http://bs.baidu.com/dulife/54364925562cc.jpg"
    downloadFile(target_url, "1")

