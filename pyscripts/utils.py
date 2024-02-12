import os
import sys
import time
import zipfile

import requests

# Import win32api

'''

 Support :
     chlocal 选择当前脚本所在目录
         无参数
     str2hex 将字符串转换为二进制
         需要字符串参数
     symlink 生成一个cygwin可以识别的软连接
         第一个参数是链接目标 第二个参数是生成文件
     mkdir   新建一个文件夹
         需要文件夹路径
     rmdir   递归删除一个文件夹
         需要文件夹路径
     hideDosConsole(title)
         根据标题隐藏控制台
     showDosConsole(title)
         根据标题显示控制台
     hideForegroundWindow
         隐藏最顶层控制台
     addExecPath(addpath)
         在PATH路径增加一个目录
     get_time()
         返回当前时间
     listdir(path,ext)
         path 路径
         ext 文件扩展名
     runcmd(cmd)
         运行系统中的命令，不支持中文返回
     getShiju()
         获取诗句

'''
formats = ([b'PK', "zip"], [b'OPPOENCRYPT!', "ozip"], [b'7z', "7z"], [b'\x53\xef', 'ext', 1080],
           [b'\x3a\xff\x26\xed', "sparse"], [b'\xe2\xe1\xf5\xe0', "erofs", 1024], [b"CrAU", "payload"],
           [b"AVB0", "vbmeta"], [b'\xd7\xb7\xab\x1e', "dtbo"],
           [b'\xd0\x0d\xfe\xed', "dtb"], [b"MZ", "exe"], [b".ELF", 'elf'],
           [b"ANDROID!", "boot"], [b"VNDRBOOT", "vendor_boot"],
           [b'AVBf', "avb_foot"], [b'BZh', "bzip2"],
           [b'CHROMEOS', 'chrome'], [b'\x1f\x8b', "gzip"],
           [b'\x1f\x9e', "gzip"], [b'\x02\x21\x4c\x18', "lz4_legacy"],
           [b'\x03\x21\x4c\x18', 'lz4'], [b'\x04\x22\x4d\x18', 'lz4'],
           [b'\x1f\x8b\x08\x00\x00\x00\x00\x00\x02\x03', "zopfli"], [b'\xfd7zXZ', 'xz'],
           [b']\x00\x00\x00\x04\xff\xff\xff\xff\xff\xff\xff\xff', 'lzma'], [b'\x02!L\x18', 'lz4_lg'],
           [b'\x89PNG', 'png'], [b"LOGO!!!!", 'logo'])


def gettype(file) -> str:
    if not os.path.exists(file):
        return "fne"

    def compare(header: bytes, number: int = 0) -> int:
        with open(file, 'rb') as f:
            f.seek(number)
            return f.read(len(header)) == header

    def is_super(fil) -> any:
        with open(fil, 'rb') as file_:
            buf = bytearray(file_.read(4))
            if len(buf) < 4:
                return False
            file_.seek(0, 0)

            while buf[0] == 0x00:
                buf = bytearray(file_.read(1))
            try:
                file_.seek(-1, 1)
            except:
                return False
            buf += bytearray(file_.read(4))
        return buf[1:] == b'\x67\x44\x6c\x61'

    try:
        if is_super(file):
            return 'super'
    except IndexError:
        pass
    for f_ in formats:
        if len(f_) == 2:
            if compare(f_[0]):
                return f_[1]
        elif len(f_) == 3:
            if compare(f_[0], f_[2]):
                return f_[1]
    if '.' in file:
        return os.path.splitext(file)[1].replace(".", '')
    return "unknow"


def chLocal():
    os.chdir(os.path.abspath(os.path.dirname(sys.argv[0])))


def mkdir(path):
    folder = os.path.exists(path)
    if not folder:  # 判断是否存在文件夹如果不存在则创建为文件夹
        os.makedirs(path)  # makedirs 创建文件时如果路径不存在会创建这个路径
    else:
        return False


def get_time():  # 返回当前时间
    return time.strftime('%H:%M:%S')


def listDirHeader(path, head):
    L = []
    for i in os.listdir(path):
        if i.startswith(head):
            L.append(i)
    return L


def unzip_file(zip_src, dst_dir):
    r = zipfile.is_zipfile(zip_src)
    if r:
        fz = zipfile.ZipFile(zip_src, 'r')
        for file in fz.namelist():
            fz.extract(file, dst_dir)
    else:
        print('This is not zip')


def zip_file(file, dst_dir):
    def get_all_file_paths(directory):
        # 初始化文件路径列表
        file_paths = []
        for root, directories, files in os.walk(directory):
            for filename in files:
                # 连接字符串形成完整的路径
                filepath = os.path.join(root, filename)
                file_paths.append(filepath)

        # 返回所有文件路径
        return file_paths

    # 假设要把一个叫testdir中的文件全部添加到压缩包里（这里只添加一级子目录中的文件）
    path = os.getcwd()
    relpath = os.path.abspath(file)
    os.chdir(dst_dir)
    file_paths = get_all_file_paths('.')
    # compression
    # 生成压缩文件
    with zipfile.ZipFile(relpath, 'w', compression=zipfile.ZIP_DEFLATED, allowZip64=True) as zip:
        # 遍历写入文件
        for file in file_paths:
            zip.write(file)
    os.chdir(path)


def getShiju():
    return requests.get("https://v1.jinrishici.com/all", proxies={"http": None,
                                                                  "https": None}).json()


def getdirsize(dir):
    size = 0
    for root, dirs, files in os.walk(dir):
        size += sum([os.path.getsize(os.path.join(root, name)) for name in files])
    return size
