#!/usr/bin/env python3
import json
import os
import shutil
import subprocess
import sys
import time
import zipfile
from threading import Thread
from tkinter import *
from tkinter import scrolledtext, ttk
from tkinter.filedialog import *
from webbrowser import open as open_url

from requests import get as requests_get
from ttkbootstrap import Style
from ttkbootstrap.constants import *
from ttkbootstrap.scrolled import ScrolledFrame

from pyscripts import ozip_decrypt, imgextractor, sdat2img, fspatch, img2sdat


def checkMagic(file):
    if os.access(file, os.F_OK):
        magic = b'AVB0'
        with open(file, "rb") as f:
            buf = f.read(4)
            return magic == buf
    else:
        print("File dose not exist!")


def readVerifyFlag(file):
    if os.access(file, os.F_OK):
        with open(file, "rb") as f:
            f.seek(123, 0)
            flag = f.read(1)
            if flag == b'\x00':
                return 0
            elif flag == b'\x01':
                return 1
            elif flag == b'\x02':
                return 2
            else:
                print("Unknow")
    else:
        print("File does not exist!")


def restore(file):
    if os.access(file, os.F_OK):
        flag = b'\x00'
        with open(file, "rb+") as f:
            f.seek(123, 0)
            f.write(flag)
    else:
        print("File does not exist!")


def disableAVB(file):
    if os.access(file, os.F_OK):
        flag = b'\x02'
        with open(file, "rb+") as f:
            f.seek(123, 0)
            f.write(flag)
    else:
        print("File does not exist!")


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


def mkdir(path):
    os.makedirs(path) if not os.path.exists(path) else ...


LOCALDIR = os.getcwd()
setfile = LOCALDIR + os.sep + 'bin' + os.sep + "config.json"


class set_utils:
    def __init__(self, path):
        self.path = path

    def load(self):
        with open(self.path, 'r') as ss:
            data = json.load(ss)
            [setattr(self, v, data[v]) for v in data]

    def change(self, name, value):
        with open(self.path, 'r') as ss:
            data = json.load(ss)
        with open(self.path, 'w', encoding='utf-8') as ss:
            data[name] = value
            json.dump(data, ss, ensure_ascii=False, indent=4)
        self.load()

    def __getattr__(self, item_):
        try:
            return getattr(self, item_)
        except (Exception, BaseException):
            return ''


settings = set_utils(setfile)
settings.load()
style = Style(theme=settings.theme)
root = style.master
width = 1240
height = 600
root.geometry("%sx%s" % (width, height))
root.title("NH4RomTool")
LOGOIMG = PhotoImage(file="bin\\logo.png")
DEFAULTSTATUS = PhotoImage(file="bin\\processdone.png")

WorkDir = ''


class myStdout:
    def __init__(self):
        sys.stdout = self
        sys.stderr = self

    @staticmethod
    def write(info):
        text.configure(state='normal')
        if info != '\n':
            text.insert(END, "[%s]%s\n" % (time.strftime('%H:%M:%S'), info))
        text.update()
        text.yview('end')
        text.configure(state='disabled')

    def flush(self):
        ...


def runcmd(cmd):
    if not os.path.exists(cmd.split()[0]):
        cmd = os.path.join(LOCALDIR, 'bin') + os.sep + cmd
    try:
        ret = subprocess.Popen(cmd, shell=False,
                               stdin=subprocess.PIPE,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT)
        for i in iter(ret.stdout.readline, b""):
            print(i.decode("utf-8", "ignore").strip())
    except subprocess.CalledProcessError as e:
        for i in iter(e.stdout.readline, b""):
            print(i)


def about():
    root2 = Toplevel()
    root2.resizable(False, False)
    root2.title("关于")
    aframe1 = Frame(root2, relief=FLAT, borderwidth=1)
    aframe2 = Frame(root2, relief=FLAT, borderwidth=1)
    aframe1.pack(side=BOTTOM, pady=3)
    aframe2.pack(side=BOTTOM, pady=3)
    ttk.Button(aframe1, text='开源地址', command=lambda: open_url("https://github.com/ColdWindScholar/NH4RomTool"),
               style='success.TButton').pack(side=LEFT, expand=YES,
                                             padx=5)
    ttk.Label(aframe2,
              text='沼_Rom工具箱\nTheme by ttkbootstrap\nColdWindSolachar Copyright(R) Apache 2.0 LICENSE',
              font=(None, 15)).pack(
        side=BOTTOM, expand=NO, pady=3)

    ttk.Label(aframe2, image=LOGOIMG).pack(side=TOP, expand=YES, pady=3)
    root2.mainloop()


def userInputWindow(title='输入文本'):
    input_window = Toplevel()
    cur_width = 400
    cur_hight = 120
    ent = StringVar()
    scn_w, scn_h = root.maxsize()
    cen_x = (scn_w - cur_width) / 2
    cen_y = (scn_h - cur_hight) / 2
    size_xy = '%dx%d+%d+%d' % (cur_width, cur_hight, cen_x, cen_y)
    input_window.geometry(size_xy)
    input_window.resizable(False, False)
    input_window.title(title)
    ent_ = ttk.Entry(input_window, textvariable=ent, width=50)
    ent_.bind("<Return>", lambda *x: input_window.destroy())
    ent_.pack(side=TOP, expand=YES, padx=5)
    ttk.Button(input_window, text='确认', command=input_window.destroy, style='primiary.Outline.TButton').pack(side=TOP,
                                                                                                               expand=YES,
                                                                                                               padx=5)
    input_window.wait_window()
    return ent.get()


def change_theme(var):
    print("设置主题为 : " + var)
    Style(theme=var).theme_use()
    settings.change('theme', var)


def getWorkDir():
    for i in table.get_children():
        table.delete(i)
    for i in os.listdir(LOCALDIR):
        if i.startswith('NH4'):
            table.insert('', 'end', value=i)


def clearWorkDir():
    if not WorkDir:
        print("当前未选择任何目录")
    else:
        if not os.path.exists(WorkDir):
            return
        print("将清理: " + WorkDir)
        try:
            for i in os.listdir(WorkDir):
                if os.path.isdir(os.path.join(WorkDir, i)):
                    shutil.rmtree(os.getcwd() + os.sep + WorkDir)
                if os.path.isfile(os.path.join(WorkDir, i)):
                    os.remove(os.path.join(WorkDir, i))
        except IOError:
            print("清理失败, 请检查是否有程序正在占用它...?")
        else:
            print("清理成功, 正在刷新工作目录")


class cartoon:
    def __init__(self):
        ...

    def __enter__(self):
        self.state = False
        self.statusthread = Thread(target=self.__run)
        self.statusthread.start()

    def __run(self):
        while True:
            for i in range(33):  # 33是图片帧数
                photo = PhotoImage(file=LOCALDIR + '\\bin\\processing.gif', format='gif -index %i' % i)
                statusbar['image'] = photo
                time.sleep(1 / 18)
            if self.state:
                break

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.state = True
        self.statusthread.join()
        statusbar['image'] = DEFAULTSTATUS


def SelectWorkDir():
    item_text = ['']
    for item_ in table.selection():
        item_text = table.item(item_, "values")
    if item_text[0]:
        global WorkDir
        WorkDir = item_text[0]
        print("选择工作目录为: %s" % WorkDir)


def rmWorkDir():
    if WorkDir:
        print("删除目录: %s" % WorkDir)
        shutil.rmtree(WorkDir)
    else:
        print("Error : 要删除的文件夹不存在")
    getWorkDir()


def mkWorkdir():
    mkdir(f'NH4_{userInputWindow()}')
    getWorkDir()


def __ozipEncrypt():
    filename = askopenfilename(title="加密ozip")
    if os.access(filename, os.F_OK):
        with cartoon():
            runcmd("zip2ozip " + filename)
    else:
        print("Error : 文件不存在")


def __unzipfile():
    if WorkDir:
        if os.access(WorkDir + os.sep + "rom", os.F_OK):
            shutil.rmtree(WorkDir + os.sep + "rom")
        filename = askopenfilename(title="选择要解压的文件")
        if os.access(filename, os.F_OK):
            print("正在解压文件: " + filename)
            with cartoon():
                zipfile.ZipFile(filename, 'r').extractall(WorkDir + os.sep + "rom") if zipfile.is_zipfile(
                    filename) else print('This is not zip')
            print("解压完成")
        else:
            print("Error : 文件不存在")
    else:
        print("Error : 请先选择工作目录")


def zip_file(file, dst_dir):
    def get_all_file_paths(directory):
        for root, directories, files in os.walk(directory):
            for filename in files:
                yield os.path.join(root, filename)

    path = os.getcwd()
    os.chdir(dst_dir)
    with zipfile.ZipFile(os.path.abspath(file), 'w', compression=zipfile.ZIP_DEFLATED, allowZip64=True) as zip:
        # 遍历写入文件
        for f in get_all_file_paths('.'):
            zip.write(f)
    os.chdir(path)


def __zipcompressfile():
    print("输入生成的文件名")
    inputvar = userInputWindow()
    if WorkDir:
        print("正在压缩 : " + inputvar + ".zip")
        with cartoon():
            cz(zip_file, inputvar + ".zip", WorkDir + os.sep + "rom")
        print("压缩完成")
    else:
        print("Error : 请先选择工作目录")


def patchvbmeta():
    filename = askopenfilename(title="选择vbmeta文件")
    if os.access(filename, os.F_OK):
        if checkMagic(filename):
            flag = readVerifyFlag(filename)
            if flag == 0:
                print("检测到AVB为打开状态，正在关闭...")
                disableAVB(filename)
            elif flag == 1:
                print("检测到仅关闭了DM校验，正在关闭AVB...")
                disableAVB(filename)
            elif flag == 2:
                print("检测AVB校验已关闭，正在开启...")
                restore(filename)
            else:
                print("未知错误")
        else:
            print("文件并非vbmeta文件")
    else:
        print("文件不存在")


def cz(func, *args):
    Thread(target=func, args=args, daemon=True).start()


def __smartUnpack():
    with cartoon():
        filename = askopenfilename(title="选择解包的文件")
        if WorkDir:
            if os.access(filename, os.F_OK):
                filetype = gettype(filename)
                print("智能识别文件类型为 :  " + filetype)
                unpackdir = os.path.abspath(WorkDir + "/" + filetype)
                if filetype == "ozip":
                    print("正在解密ozip")
                    ozip_decrypt.main(filename)
                    print("解密完成")
                if filetype in ["ext", "erofs"]:
                    dirname = os.path.basename(filename).split(".")[0]

                    print("在工作目录创建解包目录 : " + dirname)
                    if os.path.isdir(os.path.abspath(WorkDir) + "/" + dirname):
                        print("文件夹存在，正在删除")
                        shutil.rmtree(os.path.abspath(WorkDir) + "/" + dirname)
                    mkdir(os.path.abspath(WorkDir) + "/" + dirname)

                    if filetype == "ext":
                        print("正在解包[ext]: " + filename)
                        imgextractor.Extractor().main(filename, WorkDir + os.sep + dirname + os.sep +
                                                      os.path.basename(filename).split('.')[0])
                    if filetype == "erofs":
                        print("正在解包[erofs]: " + filename)
                        runcmd(f"extract.erofs.exe -i {filename} -o {WorkDir + os.sep + dirname} -x")

                else:
                    for i in ["super", "dtbo", "boot", "payload"]:
                        if filetype == i:
                            print("在工作目录创建解包目录 :  " + i)
                            if os.path.isdir(unpackdir):
                                print("文件夹存在，正在删除")
                                shutil.rmtree(unpackdir)
                            mkdir(unpackdir)
                            if i == "payload":
                                print("正在解包payload")
                                t = Thread(target=runcmd, args=[
                                    "payload-dumper-go.exe -o %s\\payload %s" % (WorkDir, filename)],
                                           daemon=True)
                                t.start()
                                t.join()
                            if i == "boot":
                                print("正在解包boot")
                                os.chdir(unpackdir)
                                shutil.copy(filename, os.path.join(unpackdir, os.path.basename(filename)))
                                runcmd("magiskboot unpack -h %s" % filename)
                                if os.path.exists('ramdisk.cpio'):
                                    comp = gettype("ramdisk.cpio")
                                    print("Ramdisk is %s" % comp)
                                    with open("comp", "w") as f:
                                        f.write(comp)
                                    if comp != "unknow" and comp != 'cpio':
                                        runcmd("magiskboot decompress ramdisk.cpio ramdisk.raw")
                                        os.remove('ramdisk.cpio')
                                        os.rename('ramdisk.raw', 'ramdisk.cpio')
                                    os.makedirs('ramdisk')
                                    runcmd("cpio -i -d -F %s -D %s" % ("ramdisk.cpio", "ramdisk"))
                                os.chdir(LOCALDIR)
                            if i == "dtbo":
                                print("使用mkdtboimg解包")
                                runcmd("mkdtboimg.exe dump " + filename + " -b " + unpackdir + "\\dtb")
                            if i == "super":
                                print("使用 lpunpack 解锁")
                                runcmd("lpunpack " + filename + " " + unpackdir)
                    if filetype == "sparse":
                        print("正在转换Sparse-->Raw")

                        mkdir(WorkDir + "\\rawimg")
                        runcmd("simg2img " + filename + " " + WorkDir + "\\rawimg\\" + os.path.basename(
                            filename))
                        print("sparse image 转换结束")
                    if filetype == "dat":
                        print("正在解包Dat")
                        pname = os.path.basename(filename).split(".")[0]
                        transferpath = os.path.abspath(
                            os.path.dirname(filename)) + os.sep + pname + ".transfer.list"
                        if os.access(transferpath, os.F_OK):
                            with cartoon():
                                sdat2img.sdat2img(transferpath, filename, WorkDir + os.sep + pname + ".img")
                                print("sdat已转换为img")
                        else:
                            print("未能在dat文件所在目录找到对应的transfer.list文件")
                    if filetype == "br":
                        print("检测到br格式，使用brotli解压")
                        pname = os.path.basename(filename).replace(".br", "")
                        if os.access(filename, os.F_OK):
                            with cartoon():
                                runcmd("brotli -d " + filename + " " + WorkDir + os.sep + pname)
                            print("已解压br文件")
                        else:
                            print("文件不可访问！")
                    if filetype == "dtb":
                        print("使用device tree compiler 转换反编译dtb --> dts")
                        dtname = os.path.basename(filename)
                        runcmd("dtc -q -I dtb -O dts " + filename + " -o " + WorkDir + os.sep + dtname + ".dts")
                        print("反编译dtb完成")
                    if filetype in ["zip"]:
                        print("请使用解压功能解压zip")
                    if filetype == "Unknow":
                        print("文件不受支持")
            else:
                print("文件不存在")
        else:
            print("请先选择工作目录")


def repackboot():
    directoryname = askdirectory(title="选择你要打包的目录")
    if os.path.isdir(directoryname):
        os.chdir(directoryname)
        if os.path.exists('ramdisk'):
            os.chdir('ramdisk')
            runcmd("busybox ash -c \"find | sed 1d | %s -H newc -R 0:0 -o -F ../ramdisk-new.cpio\"" % os.path.realpath(
                LOCALDIR + '/bin/cpio.exe').replace('\\', '/'))
            os.chdir(directoryname)
            with open("comp", "r", encoding='utf-8') as compf:
                comp = compf.read()
            print("Compressing:%s" % comp)
            if comp != 'cpio':
                runcmd("magiskboot compress=%s ramdisk-new.cpio" % comp)
                if os.path.exists('ramdisk.cpio'):
                    os.remove('ramdisk.cpio')
                os.rename("ramdisk-new.cpio.%s" % comp.split('_')[0], "ramdisk.cpio")
            else:
                if os.path.exists('ramdisk.cpio'):
                    os.remove('ramdisk.cpio')
                os.rename("ramdisk-new.cpio", "ramdisk.cpio")
        runcmd("magiskboot repack boot.img")
        if os.path.exists('boot.img'):
            os.remove('boot.img')
        shutil.copyfile("new-boot.img", os.path.join(LOCALDIR, WorkDir, 'boot.img'))
        os.chdir(LOCALDIR)
        shutil.rmtree(directoryname)
    else:
        print("文件夹不存在")


def find_fs_con(directoryname):
    is_fs_config = fs_config if os.path.exists((fs_config := os.path.join(directoryname, '..', 'config',
                                                                          f'{os.path.basename(directoryname)}_fs_config'))) else ''
    is_fs_config = os.path.realpath(is_fs_config)
    is_file_contexts = fs_config if os.path.exists((fs_config := os.path.join(directoryname, '..', 'config',
                                                                              f'{os.path.basename(directoryname)}_file_contexts'))) else ''
    is_file_contexts = os.path.realpath(is_file_contexts)
    if is_fs_config and not os.path.isdir(is_fs_config):
        print("自动搜寻 fs_config 完成: " + is_fs_config)
        fsconfig_path = is_fs_config
    else:
        print("自动搜寻 fs_config 失败，请手动选择")
        fsconfig_path = askopenfilename(title="选择你要打包目录的fs_config文件")
    if is_file_contexts and not os.path.isdir(is_file_contexts):
        print("自动搜寻 file_contexts 完成" + is_file_contexts)
        filecontexts_path = is_file_contexts
    else:
        print("自动搜寻 fs_context 失败，请手动选择")
        filecontexts_path = askopenfilename(title="选择你要打包目录的fs_context文件")
    print("修补fs_config文件")
    fspatch.main(directoryname, fsconfig_path)
    return filecontexts_path, fsconfig_path


def getdirsize(dir_):
    size = 0
    for root, dirs, files in os.walk(dir_):
        size += sum([os.path.getsize(os.path.join(root, name)) for name in files])
    return size


def __repackextimage():
    if WorkDir:
        directoryname = askdirectory(title="选择你要打包的目录 例如:.\\NH4_t\\vendor\\vendor")
        filecontexts_path, fsconfig_path = find_fs_con(directoryname)
        if os.path.isdir(directoryname):
            mutiimgsize = 1.2 if os.path.basename(directoryname).find("odm") != -1 else 1.07
            if settings.automutiimgsize:
                extimgsize = int(getdirsize(directoryname) * mutiimgsize)
            else:
                size = f if os.path.exists((f := os.path.join(directoryname, '..', 'config',
                                                              f'{os.path.basename(directoryname)}_size.txt'))) else ''
                size = os.path.realpath(size)
                if os.path.isfile(size):
                    with open(size, 'r') as z:
                        extimgsize = int(z.read())
                else:
                    extimgsize = settings.modifiedimgsize
            part_name = os.path.basename(directoryname)
            cmd = f"mke2fs.exe -O {settings.extfueature} -L {part_name} -I 256 -M /{part_name} -m 0"
            cmd += f" -t {settings.extrepacktype} -b {settings.extblocksize} {WorkDir}/output/{part_name}.img {int(extimgsize / 4096)}"
            print("尝试创建目录output")
            mkdir(WorkDir + os.sep + "output")
            print("开始打包EXT镜像")
            with cartoon():
                print(cmd)
                runcmd(cmd)
                cmd = f"e2fsdroid.exe -e -T 1230768000 -C {fsconfig_path} -S {filecontexts_path} -f {directoryname} -a /{part_name} {WorkDir}/output/{part_name}.img"
                runcmd(cmd)
                print("打包结束")
    else:
        print("请先选择工作目录")


def __repackerofsimage():
    if WorkDir:
        directoryname = askdirectory(title="选择你要打包的目录 例如 : .\\NH4_test\\vendor\\vendor")
        filecontexts_path, fsconfig_path = find_fs_con(directoryname)
        with cartoon():
            fspatch.main(directoryname, fsconfig_path)
            cmd = "mkfs.erofs.exe %s/output/%s.img %s -z\"%s\" -T\"1230768000\" --mount-point=/%s --fs-config-file=%s --file-contexts=%s" % (
                WorkDir, os.path.basename(directoryname), directoryname.replace("\\", "/"),
                settings.erofstype, os.path.basename(directoryname), fsconfig_path, filecontexts_path)
            print(cmd)
            runcmd(cmd)
    else:
        print("请先选择工作目录")


def __repackDTBO():
    if WorkDir:
        directoryname = askdirectory(title="选择dtbo文件夹")
        if not os.path.isdir(WorkDir + os.sep + "output"):
            mkdir(WorkDir + os.sep + "output")
        cmd = "mkdtboimg.exe create %s\\output\\dtbo.img " % WorkDir
        for i in range(len([i for i in os.listdir(directoryname)])):
            cmd += "%s\\dtb.%s " % (directoryname, i)
        runcmd(cmd)
        print("打包结束")
    else:
        print("请先选择工作目录")


def __repackSparseImage():
    if WorkDir:
        img_file_path = askopenfilename(title="选择要转换为 SIMG 的 IMG 文件")
        if not os.path.exists(img_file_path):
            print("文件不存在: " + img_file_path)
        elif gettype(img_file_path) != "ext":
            print("选中的文件并非 EXT 镜像，请先转换")
            return
        else:
            print("开始转换")
            with cartoon():
                cmd = "img2simg %s %s/output/%s_sparse.img" % (
                    img_file_path, WorkDir, os.path.basename(img_file_path.replace('.img', '')))
                runcmd(cmd)
                print("转换结束")
    else:
        print("请先选择工作目录")


def __compressToBr():
    if WorkDir:
        img_file_path = askopenfilename(title="选择要转换为 BR 的 DAT 文件")
        if not os.path.exists(img_file_path):
            print("文件不存在: " + img_file_path)
        elif gettype(img_file_path) != "dat":
            print("选中的文件并非 DAT，请先转换")
            return
        else:
            print("开始转换")
            with cartoon():
                cz(runcmd, "brotli.exe -q 6 " + img_file_path)
            print("转换完毕，脱出到相同文件夹")
    else:
        print("请先选择工作目录")


def __repackDat():
    if WorkDir:
        img_file_path = askopenfilename(title="选择要转换为 DAT 的 IMG 文件")
        if not os.path.exists(img_file_path):
            print("文件不存在: " + img_file_path)
        elif gettype(img_file_path) != "sparse":
            print("选中的文件并非 SPARSE，请先转换")
            return
        else:
            print("警告: 只接受大版本输入，例如 7.1.2 请直接输入 7.1！")
            input_version = float(userInputWindow("输入Android版本"))
            current_version = 0
            if input_version == 5.0:  # Android 5
                print("已选择: Android 5.0")
                current_version = 1
            elif input_version == 5.1:  # Android 5.1
                print("已选择: Android 5.1")
                current_version = 2
            elif 6.0 <= input_version < 7.0:  # Android 6.X
                print("已选择: Android 6.X")
                current_version = 3
            elif input_version >= 7.0:  # Android 7.0+
                print("已选择: Android 7.X+")
                current_version = 4
            print("提示: 输入分区名 (例如 system、vendor、odm)")
            partition_name = userInputWindow("输入分区名")
            if current_version == 0:
                print("Android 版本输入错误，请查看提示重新输入！")
                return
            elif partition_name == 0 or not partition_name:
                print("分区名输入错误，请查看提示重新输入！")
                return
            print("开始转换")
            with cartoon():
                cz(img2sdat.main, img_file_path, WorkDir + "/output/", current_version, partition_name)
            print("转换完毕，脱出到工作目录下 output 文件夹")
    else:
        print("请先选择工作目录")


def __repackdtb():
    if WorkDir:
        filename = askopenfilename(title="选择dts文件，输出到dtb文件夹")
        if os.access(filename, os.F_OK):
            if not os.path.isdir(WorkDir + os.sep + "dtb"):
                mkdir(WorkDir + os.sep + "dtb")
            with cartoon():
                runcmd("dtc -I dts -O dtb %s -o %s\\dtb\\%s.dtb" % (
                    filename, WorkDir, os.path.basename(filename).replace(".dts", ".dtb")))
            print("编译为dtb完成")
        else:
            print("文件不存在")
    else:
        print("请先选择工作目录")


def __repackSuper():
    if WorkDir:
        packtype = StringVar(value='VAB')
        packsize = StringVar(value="9126805504")
        packgroup = StringVar(value='main')
        img_dir = StringVar()
        sparse = IntVar()
        w = Toplevel()
        cur_width = 400
        cur_hight = 450
        scn_w, scn_h = root.maxsize()
        cen_x = (scn_w - cur_width) / 2
        cen_y = (scn_h - cur_hight) / 2
        size_xy = '%dx%d+%d+%d' % (cur_width, cur_hight, cen_x, cen_y)
        w.geometry(size_xy)
        w.resizable(False, False)
        w.title("打包Super")
        l1 = ttk.LabelFrame(w, text="分区类型", labelanchor="nw", relief=GROOVE, borderwidth=1)
        ttk.Radiobutton(l1, variable=packtype, value='VAB', text='VAB').pack(side=LEFT, expand=YES, padx=5)
        ttk.Radiobutton(l1, variable=packtype, value='AB', text='AB').pack(side=LEFT, expand=YES, padx=5)
        ttk.Radiobutton(l1, variable=packtype, value='A-only', text='A-only').pack(side=LEFT, expand=YES, padx=5)
        l1.pack(side=TOP, ipadx=10, ipady=10)
        ttk.Label(w, text="super分区大小(字节 常见9126805504)").pack(side=TOP)
        ttk.Entry(w, textvariable=packsize, width=50).pack(side=TOP, padx=10, pady=10, expand=YES, fill=BOTH)
        ttk.Label(w, text="super分区簇名").pack()
        ttk.Entry(w, textvariable=packgroup, width=50).pack(side=TOP, padx=10, pady=10, expand=YES, fill=BOTH)
        l2 = ttk.Labelframe(w, text="镜像文件夹:", labelanchor="nw", relief=GROOVE, borderwidth=1)
        ttk.Entry(l2, textvariable=img_dir, width=50).pack(padx=10, pady=10, fill=X)
        ttk.Button(l2, text="浏览",
                   command=lambda: img_dir.set(askdirectory(title="选择super分区镜像文件所在目录"))).pack()
        l2.pack(ipadx=10, ipady=10)
        Checkbutton(w, text="Sparse", variable=sparse).pack(side=TOP, padx=10, pady=10)
        Button(w, text="打包", command=w.destroy, width=20, height=20).pack(padx=10, pady=10)
        w.wait_window()
        if not packtype.get():
            print("没有获取到选项")
        else:
            superdir = img_dir.get()
            if not superdir or not os.path.join(superdir):
                print("目录不存在")
                return
            print("super分区镜像所在目录：" + superdir)
            if sparse.get():
                print("启用sparse参数")
            cmd = "lpmake "
            print("打包类型 ： " + packtype.get())
            cmd += "--metadata-size 65536 --super-name super "
            if packtype.get() == 'VAB':
                cmd += "--virtual-ab "
            if sparse.get():
                cmd += "--sparse "
            cmd += f"--metadata-slots {'2' if packtype.get() in ['AB', 'A-only'] else '3'} "
            cmd += "--device super:%s " % (packsize.get())
            if packtype.get() in ['VAB', 'AB']:
                cmd += '--group %s_a:%s ' % (packgroup.get(), packsize.get())
                super_parts = []
                for i in os.listdir(superdir):
                    if os.path.isfile(os.path.join(superdir, i)) and i.endswith('.img'):
                        part_name = os.path.basename(i).replace('.img', '')
                        super_parts.append(part_name)
                        cmd += "--partition %s_a:readonly:%s:%s_a --image %s_a=%s " % (
                            part_name, os.path.getsize(os.path.join(superdir, i)),
                            packgroup.get(), part_name, os.path.join(superdir, i))
                cmd += '--group %s_b:%s ' % (packgroup.get(), packsize.get())
                for i in super_parts:
                    cmd += '--partition %s_b:readonly:0:%s_b ' % (i, packgroup.get())
            else:
                cmd += '--group %s:%s ' % (packgroup.get(), packsize.get())
                for i in os.listdir(superdir):
                    if os.path.isfile(os.path.join(superdir, i)) and i.endswith('.img'):
                        cmd += "--partition %s:readonly:%s:%s --image %s=%s " % (
                            os.path.basename(i).replace('.img', ''), os.path.getsize(os.path.join(superdir, i)),
                            packgroup.get(), os.path.basename(i).replace('.img', ''), os.path.join(superdir, i))
            cmd += '--out %s' % (os.path.join(WorkDir, 'super.img'))
            runcmd(cmd)
            print("打包成功") if os.path.join(WorkDir, 'super.img') else print("打包失败")

    else:
        print("请先选择工作目录")


if __name__ == '__main__':
    myStdout()
    screenwidth = root.winfo_screenwidth()
    screenheight = root.winfo_screenheight()
    root.geometry(
        '{}x{}+{}+{}'.format(width, height, int((screenwidth - width) / 2), int((screenheight - height) / 2)))
    menuBar = Menu(root)
    root.config(menu=menuBar)
    menu1 = Menu(menuBar, tearoff=False)
    menu1.add_command(label="关于", command=about)
    menu1.add_command(label="退出", command=sys.exit)
    menuBar.add_cascade(label="菜单", menu=menu1)
    menu2 = Menu(menuBar, tearoff=False)
    menuItem = ["cosmo", "flatly", "journal", "literal", "lumen", "minty", "pulse", "sandstone", "united", "yeti",
                "cyborg", "darkly", "solar", "vapor", "superhero"]
    for item in menuItem:
        menu2.add_command(label=item, command=lambda n=item: change_theme(n))
    menuBar.add_cascade(label="主题", menu=menu2)
    frame = ttk.LabelFrame(root, text="NH4 Rom Tool", labelanchor="nw", relief=GROOVE, borderwidth=1)
    frame1 = ttk.LabelFrame(frame, text="功能区", labelanchor="nw", relief=SUNKEN, borderwidth=1)
    frame2 = ttk.LabelFrame(frame, text="日志", labelanchor="nw", relief=SUNKEN, borderwidth=1)
    tabControl = ttk.Notebook(frame1)
    tab1 = ttk.Frame(tabControl)
    tab2 = ttk.Frame(tabControl)
    tab3 = ttk.Frame(tabControl)
    tab33 = ScrolledFrame(tab3, autohide=True, width=220)
    tab4 = ttk.Frame(tabControl)
    tabControl.add(tab1, text="项目")
    tabControl.add(tab2, text="打包解包")
    tabControl.add(tab3, text="其他")
    tab33.pack(side=LEFT, expand=YES, fill=BOTH)
    tab11 = ttk.Frame(tab1)
    table = ttk.Treeview(tab11, height=10, columns=["Workdir"], show='headings')
    table.column('Workdir', width=100, anchor='center')
    table.heading('Workdir', text='项目')
    table.pack(side=TOP, fill=BOTH, expand=YES)
    table.bind('<ButtonRelease-1>', lambda *x_: SelectWorkDir())
    getWorkDir()
    tab12 = ttk.Frame(tab1)
    ttk.Button(tab12, text='确认', width=10,
               command=lambda: tabControl.select(tab2) if WorkDir else print("请选择项目"),
               style='primiary.Outline.TButton').grid(row=0,
                                                      column=0,
                                                      padx=10,
                                                      pady=8)
    ttk.Button(tab12, text='删除', width=10, command=rmWorkDir, style='primiary.Outline.TButton').grid(row=0,
                                                                                                       column=1,
                                                                                                       padx=10,
                                                                                                       pady=8)
    ttk.Button(tab12, text='新建', width=10, command=mkWorkdir, style='primiary.Outline.TButton').grid(row=1,
                                                                                                       column=0,
                                                                                                       padx=10,
                                                                                                       pady=8)
    ttk.Button(tab12, text='刷新', width=10, command=getWorkDir, style='primiary.Outline.TButton').grid(row=1,
                                                                                                        column=1,
                                                                                                        padx=10,
                                                                                                        pady=8)
    ttk.Button(tab12, text='清理', width=10, command=clearWorkDir, style='primiary.Outline.TButton').grid(row=2,
                                                                                                          column=0,
                                                                                                          padx=10,
                                                                                                          pady=8)
    tab12.pack(side=BOTTOM, fill=BOTH, expand=YES, anchor=CENTER)
    tabControl.pack(fill=BOTH, expand=YES)
    tab11.pack(side=TOP, fill=BOTH, expand=YES)
    tab21 = ttk.LabelFrame(tab2, text="解包", labelanchor="nw", relief=SUNKEN, borderwidth=1)
    ttk.Button(tab21, text='解压', width=10, command=lambda: cz(__unzipfile), style='primiary.Outline.TButton').grid(
        row=0, column=0,
        padx=10,
        pady=8)
    ttk.Button(tab21, text='万能解包', width=10, command=lambda: cz(__smartUnpack),
               style='primiary.Outline.TButton').grid(row=0,
                                                      column=1,
                                                      padx=10,
                                                      pady=8)
    tab22 = ttk.LabelFrame(tab2, text="打包", labelanchor="nw", relief=SUNKEN, borderwidth=1)
    ttk.Button(tab22, text='压缩', width=10, command=lambda: cz(__zipcompressfile),
               style='primiary.Outline.TButton').grid(row=0,
                                                      column=0,
                                                      padx=10,
                                                      pady=8)
    ttk.Button(tab22, text='BOOT', width=10, command=repackboot, style='primiary.Outline.TButton').grid(row=0, column=1,
                                                                                                        padx=10,
                                                                                                        pady=8)
    ttk.Button(tab22, text='EXT', width=10, command=lambda: cz(__repackextimage),
               style='primiary.Outline.TButton').grid(row=1,
                                                      column=0,
                                                      padx=10,
                                                      pady=8)
    ttk.Button(tab22, text='EROFS', width=10, command=lambda: cz(__repackerofsimage),
               style='primiary.Outline.TButton').grid(row=1,
                                                      column=1,
                                                      padx=10,
                                                      pady=8)
    ttk.Button(tab22, text='DTS2DTB', width=10, command=lambda: cz(__repackdtb), style='primiary.Outline.TButton').grid(
        row=2,
        column=0,
        padx=10,
        pady=8)
    ttk.Button(tab22, text='DTBO', width=10, command=lambda: cz(__repackDTBO), style='primiary.Outline.TButton').grid(
        row=2, column=1,
        padx=10,
        pady=8)
    ttk.Button(tab22, text='SUPER', width=10, command=lambda: cz(__repackSuper), style='primiary.Outline.TButton').grid(
        row=3,
        column=0,
        padx=10,
        pady=8)
    ttk.Button(tab22, text='EXT->SIMG', width=10, command=lambda: cz(__repackSparseImage),
               style='primiary.Outline.TButton').grid(
        row=3, column=1, padx=10, pady=8)
    ttk.Button(tab22, text='IMG->DAT', width=10, command=lambda: cz(__repackDat),
               style='primiary.Outline.TButton').grid(row=4,
                                                      column=0,
                                                      padx=10,
                                                      pady=8)
    ttk.Button(tab22, text='DAT->BR', width=10, command=lambda: cz(__compressToBr),
               style='primiary.Outline.TButton').grid(row=4,
                                                      column=1,
                                                      padx=10,
                                                      pady=8)
    tab21.pack(side=TOP, fill=BOTH)
    tab22.pack(side=TOP, fill=BOTH, expand=YES)
    for t, c in (("检测文件格式", lambda: print(
            f"文件格式为 : {gettype(filename)}" if os.access((filename := askopenfilename(title="检测文件类型")),
                                                             os.F_OK) else "Error : 文件不存在")), ('OZIP 解密',
                                                                                                    lambda: ozip_decrypt.main(
                                                                                                        filename) if os.access(
                                                                                                        (
                                                                                                                filename := askopenfilename(
                                                                                                                    title="解密ozip")),
                                                                                                        os.F_OK) else print(
                                                                                                        "Error : 文件不存在")),
                 ('OZIP 加密', lambda: cz(__ozipEncrypt)), ('关闭 VBMETA 校验', patchvbmeta),
                 ('修补 FS_CONFIG 文件', lambda: cz(fspatch.main, askdirectory(title="选择你要打包的目录"),
                                                    askopenfilename(title="选择fs_config文件")))):
        ttk.Button(tab33, text=t, width=10, command=c, bootstyle="link").pack(
            side=TOP, expand=NO,
            fill=X, padx=8)
    text = scrolledtext.ScrolledText(frame2, width=180, height=18, font=['Arial', 10], relief=SOLID)
    text.pack(side=TOP, expand=YES, fill=BOTH, padx=4, pady=2)
    frame22 = ttk.LabelFrame(frame2, text="输入自定义命令", labelanchor="nw", relief=SUNKEN, borderwidth=1)


    def run_cmd():
        cmd = usercmd.get()
        if not cmd:
            return
        for i in ["bash", 'ash', 'cmd']:
            if i in cmd.split()[0]:
                print("这种命令会阻塞窗口， 所以终止执行")
                return
        runcmd("busybox ash -c \"%s\"" % cmd)
        usercmd.delete(0, 'end')


    usercmd = ttk.Entry(frame22, width=25)
    usercmd.pack(side=LEFT, expand=YES, fill=X, padx=2, pady=2)
    usercmd.bind('<Return>', lambda *x: run_cmd())
    ttk.Button(frame22, text='运行', command=run_cmd, style='primary.Outline.TButton').pack(side=LEFT, expand=NO,
                                                                                            fill=X, padx=2,
                                                                                            pady=2)
    frame.pack(side=TOP, expand=YES, fill=BOTH, padx=2, pady=2)
    frame1.pack(side=LEFT, expand=YES, fill=BOTH, padx=5, pady=2)
    frame2.pack(side=LEFT, expand=YES, fill=BOTH, padx=5, pady=2)
    frame22.pack(side=TOP, expand=NO, fill=BOTH, padx=5, pady=2)
    framebotm = ttk.Frame(root, relief=FLAT, borderwidth=0)


    def clean():
        text.configure(state='normal')
        text.delete(1.0, END)
        text.configure(state='disabled')


    ttk.Button(framebotm, text='清空', command=clean, style='secondary.TButton').pack(side=RIGHT, padx=5, pady=0)
    statusbar = ttk.Label(framebotm, relief='flat', anchor=E, image=DEFAULTSTATUS, bootstyle="info")
    statusbar.pack(side=RIGHT, fill=X, ipadx=12)


    def SHOWSHIJU():
        shiju = requests_get("https://v1.jinrishici.com/all", proxies={"http": None,
                                                                       "https": None}).json()
        ttk.Label(framebotm, text="%s —— %s  《%s》" % (shiju['content'], shiju['author'], shiju['origin']),
                  font=('微软雅黑', 12)).pack(side=LEFT, padx=8)


    cz(SHOWSHIJU)
    framebotm.pack(side=BOTTOM, expand=NO, fill=X, padx=8, pady=12)
    cz(root.iconbitmap, "bin\\logo.ico")
    root.mainloop()
