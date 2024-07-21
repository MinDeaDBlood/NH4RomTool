#!/usr/bin/env python3
import json
import os
import shutil
import subprocess
import sys
import time
import zipfile            
from threading import Thread
from tkinter import PhotoImage, Menu, Toplevel, StringVar, BooleanVar, IntVar
from tkinter.ttk import Button, Entry, Frame, Checkbutton
from tkinter import scrolledtext, ttk
from tkinter.filedialog import askopenfilename, askdirectory
from webbrowser import open as open_url
from requests import get as requests_get
from ttkbootstrap import Style
from ttkbootstrap.constants import GROOVE, SUNKEN, BOTTOM, FLAT, NO, TOP, YES, LEFT, X, BOTH, END,E,SOLID, CENTER, RIGHT
from ttkbootstrap.scrolled import ScrolledFrame

from pyscripts import ozip_decrypt, imgextractor, sdat2img, fspatch, img2sdat

LOCALDIR = os.getcwd()
setfile = LOCALDIR + os.sep + 'bin' + os.sep + "config.json"


def check_magic(file):
    if os.access(file, os.F_OK):
        with open(file, "rb") as f:
            return b'AVB0' == f.read(4)
    return


def read_verify_flag(file):
    if os.access(file, os.F_OK):
        with open(file, "rb") as f:
            f.seek(123, 0)
            flag = f.read(1)
            return int(flag.hex())
    return


def write_avb(file, flag):
    if os.access(file, os.F_OK):
        with open(file, "rb+") as f:
            f.seek(123, 0)
            f.write(flag)
    return


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
            except (Exception, BaseException):
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


class SetUtils:
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


settings = SetUtils(setfile)
settings.load()

WorkDir = ''


def run_command(cmd):
    if not os.path.exists(cmd.split()[0]):
        cmd = os.path.join(LOCALDIR, 'bin') + os.sep + cmd
    try:
        ret = subprocess.Popen(cmd, shell=False,
                               stdin=subprocess.PIPE,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT)
        for i in iter(ret.stdout.readline, b""):
            try:
                print(i.decode("utf-8").strip())
            except (BaseException, Exception):
                print(i.decode("gbk", 'ignore').strip())
    except subprocess.CalledProcessError as e:
        for i in iter(e.stdout.readline, b""):
            print(i)


def about():
    root2 = Toplevel()
    root2.resizable(False, False)
    root2.title("О программе")
    aframe1 = Frame(root2, relief=FLAT, borderwidth=1)
    aframe2 = Frame(root2, relief=FLAT, borderwidth=1)
    aframe1.pack(side=BOTTOM, pady=3)
    aframe2.pack(side=BOTTOM, pady=3)
    ttk.Button(aframe1, text='Ссылка на программу', command=lambda: open_url("https://github.com/ColdWindScholar/NH4RomTool"),
               style='success.TButton').pack(side=LEFT, expand=YES,
                                             padx=5)
    ttk.Label(aframe2,
              text='沼_Rom工具箱\nTheme by ttkbootstrap\nColdWindScholar Copyright(R) Apache 2.0 LICENSE\n3590361911@qq.com',
              font=(None, 15)).pack(
        side=BOTTOM, expand=NO, pady=3)
    root2.mainloop()


def user_input_window(title='Введите текст'):
    input_window = Toplevel()
    cur_width = 400
    cur_hight = 120
    ent = StringVar()
    size_xy = '%dx%d' % (cur_width, cur_hight)
    input_window.geometry(size_xy)
    input_window.resizable(False, False)
    input_window.title(title)
    ent_ = ttk.Entry(input_window, textvariable=ent, width=50)
    ent_.bind("<Return>", lambda *x: input_window.destroy())
    ent_.pack(side=TOP, expand=YES, padx=5)
    ttk.Button(input_window, text='Принять', command=input_window.destroy, style='primiary.Outline.TButton').pack(side=TOP,
                                                                                                               expand=YES,
                                                                                                               padx=5)
    input_window.wait_window()
    return ent.get()


def change_theme(var):
    print(f"Сменить тему на : {var}")
    Style(theme=var).theme_use()
    settings.change('theme', var)


def clear_work_dir():
    if not WorkDir:
        print("Папка не выбрана")
    else:
        if not os.path.exists(WorkDir):
            return
        print("Будет очищена: " + WorkDir)
        try:
            for i in os.listdir(WorkDir):
                if os.path.isdir(os.path.join(WorkDir, i)):
                    shutil.rmtree(LOCALDIR + os.sep + WorkDir)
                if os.path.isfile(os.path.join(WorkDir, i)):
                    os.remove(os.path.join(WorkDir, i))
        except IOError:
            print("Очистка не удалась, пожалуйста, проверьте, не занята ли она какой-либо программой...?")
        else:
            print("Очистка успешно завершена, рабочая папка обновляется")


class cartoon:
    def __init__(self):
        ...

    def __enter__(self):
        self.state = False
        self.status_thread = Thread(target=self.__run)
        self.status_thread.start()

    def __run(self):
        while True:
            for i in range(33):
                photo = PhotoImage(file='bin\\processing.gif', format='gif -index %i' % i)
                statusbar['image'] = photo
                time.sleep(0.055)
            if self.state:
                break

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.state = True
        self.status_thread.join()
        statusbar['image'] = D


def ozip_encrypt():
    filename = askopenfilename(title="Зашифрованный ozip")
    if os.access(filename, os.F_OK):
        with cartoon():
            run_command(f"zip2ozip {filename}")
    else:
        print("Error : Файл не найден")


def unzip():
    if WorkDir:
        if os.access(WorkDir + os.sep + "rom", os.F_OK):
            shutil.rmtree(WorkDir + os.sep + "rom")
        filename = askopenfilename(title="Выберите файл для распаковки")
        if os.access(filename, os.F_OK):
            print("Извлечение файлов: " + filename)
            with cartoon():
                zipfile.ZipFile(filename, 'r').extractall(WorkDir + os.sep + "rom") if zipfile.is_zipfile(
                    filename) else print('This is not zip')
            print("Извлечение завершено")
        else:
            print("Error : Файл не найден")
    else:
        print("Error : Пожалуйста, выберите рабочую  папку")


def zip_file(file, dst_dir):
    def get_all_file_paths(directory):
        for root, directories, files in os.walk(directory):
            for filename in files:
                yield os.path.join(root, filename)

    os.chdir(dst_dir)
    with zipfile.ZipFile(os.path.abspath(file), 'w', compression=zipfile.ZIP_DEFLATED, allowZip64=True) as zip__:
        # 遍历写入文件
        for f in get_all_file_paths('.'):
            zip__.write(str(f))
    os.chdir(LOCALDIR)


def zip_compress():
    print("Введите название прошивки")
    input_var = user_input_window()
    if WorkDir:
        print("Сжатие : " + input_var + ".zip")
        with cartoon():
            cz(zip_file, input_var + ".zip", WorkDir + os.sep + "rom")
        print("zip архив успешно сформирован")
    else:
        print("Error : Пожалуйста, выберите рабочую  папку")


def patch_vbmeta():
    filename = askopenfilename(title="Выберите файл vbmeta")
    if os.access(filename, os.F_OK):
        if check_magic(filename):
            flag = read_verify_flag(filename)
            if flag == 0:
                print("Обнаружена проверка AVB, отключение проверки...")
                write_avb(filename, b'\x02')
            elif flag == 1:
                print("Обнаружено, что отключена только проверка DM, отключение проверки AVB...")
                write_avb(filename, b'\x02')
            elif flag == 2:
                print("Проверка AVB выключена, включение...")
                write_avb(filename, b'\x00')
            else:
                print("Неизвестная ошибка")
        else:
            print("Файл не является файлом vbmeta.")
    else:
        print("Файл не найден")


def cz(func, *args):
    Thread(target=func, args=args, daemon=True).start()


def smart_unpack():
    with cartoon():
        filename = askopenfilename(title="Выберите распакованный файл")
        if WorkDir:
            if os.access(filename, os.F_OK):
                filetype = gettype(filename)
                print("Автоматическое определение типа файла :  " + filetype)
                unpackdir = os.path.abspath(WorkDir + "/" + filetype)
                if filetype == "ozip":
                    print("Расшифровка ozip")
                    ozip_decrypt.main(filename)
                    print("Расшифровка завершена")
                if filetype in ["ext", "erofs"]:
                    dirname = os.path.basename(filename).split(".")[0]

                    print("Создание папки для распаковки в рабочей папке : " + dirname)
                    if os.path.isdir(os.path.abspath(WorkDir) + "/" + dirname):
                        print("Папка уже существует и будет удалена")
                        shutil.rmtree(os.path.abspath(WorkDir) + "/" + dirname)
                    mkdir(os.path.abspath(WorkDir) + "/" + dirname)

                    if filetype == "ext":
                        print("Разобрать [ext]: " + filename)
                        imgextractor.Extractor().main(filename, WorkDir + os.sep + dirname + os.sep +
                                                      os.path.basename(filename).split('.')[0])
                    if filetype == "erofs":
                        print("Разобрать [erofs]: " + filename)
                        cz(run_command, f"extract.erofs.exe -i {filename} -o {WorkDir + os.sep + dirname} -x")

                else:
                    for i in ["super", "dtbo", "boot", "payload"]:
                        if filetype == i:
                            print("Создание папки для распаковки в рабочей папке :  " + i)
                            if os.path.isdir(unpackdir):
                                print("Папка уже существует и будет удалена")
                                shutil.rmtree(unpackdir)
                            mkdir(unpackdir)
                            if i == "payload":
                                print("Распаковка payload")
                                t = Thread(target=run_command, args=[
                                    "payload-dumper-go.exe -o %s\\payload %s" % (WorkDir, filename)],
                                           daemon=True)
                                t.start()
                                t.join()
                            if i == "boot":
                                print("Распаковка boot")
                                os.chdir(unpackdir)
                                shutil.copy(filename, os.path.join(unpackdir, os.path.basename(filename)))
                                run_command("magiskboot unpack -h %s" % filename)
                                if os.path.exists('ramdisk.cpio'):
                                    comp = gettype("ramdisk.cpio")
                                    print("Ramdisk is %s" % comp)
                                    with open("comp", "w") as f:
                                        f.write(comp)
                                    if comp != "unknow" and comp != 'cpio':
                                        run_command("magiskboot decompress ramdisk.cpio ramdisk.raw")
                                        os.remove('ramdisk.cpio')
                                        os.rename('ramdisk.raw', 'ramdisk.cpio')
                                    os.makedirs('ramdisk')
                                    run_command("cpio -i -d -F %s -D %s" % ("ramdisk.cpio", "ramdisk"))
                                os.chdir(LOCALDIR)
                            if i == "dtbo":
                                print("Используется mkdtboimg")
                                run_command("mkdtboimg.exe dump " + filename + " -b " + unpackdir + "\\dtb")
                            if i == "super":
                                print("Используется lpunpack")
                                run_command(f"lpunpack {filename} {unpackdir}")
                    if filetype == "sparse":
                        print("Преобразование Sparse-->Raw")
                        mkdir(WorkDir + os.sep + "rawimg")
                        run_command(f"simg2img {filename} " + WorkDir + "\\rawimg\\" + os.path.basename(
                            filename))
                        print("Преобразование sparse образа завершено")
                    if filetype == "dat":
                        print("Распаковка Dat")
                        pname = os.path.basename(filename).split(".")[0]
                        transferpath = os.path.abspath(
                            os.path.dirname(filename)) + os.sep + pname + ".transfer.list"
                        if os.access(transferpath, os.F_OK):
                            with cartoon():
                                sdat2img.sdat2img(transferpath, filename, WorkDir + os.sep + pname + ".img")
                                print("sdat был преобразован в img")
                        else:
                            print("未能在dat文件所在目录找到对应的transfer.list文件")
                    if filetype == "br":
                        print("检测到br格式，使用brotli解压")
                        if os.access(filename, os.F_OK):
                            with cartoon():
                                run_command(f"brotli -dj {filename}")
                            print("已解压br文件")
                        else:
                            print("文件不可访问！")
                    if filetype == "dtb":
                        print("使用device tree compiler 转换反编译dtb --> dts")
                        dtname = os.path.basename(filename)
                        run_command("dtc -q -I dtb -O dts " + filename + " -o " + WorkDir + os.sep + dtname + ".dts")
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
    directoryname = askdirectory(title="Выберите раздел, который хотите собрать")
    if os.path.isdir(directoryname):
        os.chdir(directoryname)
        if os.path.exists('ramdisk'):
            os.chdir('ramdisk')
            run_command(
                "busybox ash -c \"find | sed 1d | %s -H newc -R 0:0 -o -F ../ramdisk-new.cpio\"" % os.path.realpath(
                    LOCALDIR + '/bin/cpio.exe').replace('\\', '/'))
            os.chdir(directoryname)
            with open("comp", "r", encoding='utf-8') as compf:
                comp = compf.read()
            print("Compressing:%s" % comp)
            if comp != 'cpio':
                run_command("magiskboot compress=%s ramdisk-new.cpio" % comp)
                if os.path.exists('ramdisk.cpio'):
                    os.remove('ramdisk.cpio')
                os.rename("ramdisk-new.cpio.%s" % comp.split('_')[0], "ramdisk.cpio")
            else:
                if os.path.exists('ramdisk.cpio'):
                    os.remove('ramdisk.cpio')
                os.rename("ramdisk-new.cpio", "ramdisk.cpio")
        run_command("magiskboot repack boot.img")
        if os.path.exists('boot.img'):
            os.remove('boot.img')
        shutil.copyfile("new-boot.img", os.path.join(LOCALDIR, WorkDir, 'boot.img'))
        os.chdir(LOCALDIR)
        shutil.rmtree(directoryname)
    else:
        print("Папка не существует")


def find_fs_con(directoryname):
    is_fs_config = fs_config if os.path.exists((fs_config := os.path.join(directoryname, '..', 'config',
                                                                          f'{os.path.basename(directoryname)}_fs_config'))) else ''
    is_fs_config = os.path.realpath(is_fs_config)
    is_file_contexts = fs_config if os.path.exists((fs_config := os.path.join(directoryname, '..', 'config',
                                                                              f'{os.path.basename(directoryname)}_file_contexts'))) else ''
    is_file_contexts = os.path.realpath(is_file_contexts)
    if is_fs_config and not os.path.isdir(is_fs_config):
        print("Автоматический поиск fs_config завершен: " + is_fs_config)
        fsconfig_path = is_fs_config
    else:
        print("Автоматический поиск fs_config не удался, пожалуйста, выберите его вручную")
        fsconfig_path = askopenfilename(title="Выберите файл fs_config в папке, которую вы хотите собрать")
    if is_file_contexts and not os.path.isdir(is_file_contexts):
        print("Автоматический поиск file_contexts завершен" + is_file_contexts)
        filecontexts_path = is_file_contexts
    else:
        print("Автоматический поиск fs_context не удался, пожалуйста, выберите его вручную")
        filecontexts_path = askopenfilename(title="Выберите файл fs_context из папки, которую вы хотите собрать")
    print("Исправление fs_config")
    fspatch.main(directoryname, fsconfig_path)
    return filecontexts_path, fsconfig_path


def getdirsize(dir_):
    size = 0
    for root, dirs, files in os.walk(dir_):
        size += sum([os.path.getsize(os.path.join(root, name)) for name in files])
    return size


def repack_ext():
    if WorkDir:
        directoryname = askdirectory(title="Выберите раздел, который хотите собрать, например:.\\NH4_t\\vendor\\vendor")
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
            print("Укажите путь к папке для сохранения образа")
            mkdir(WorkDir + os.sep + "output")
            print("Сборка EXT-образа")
            with cartoon():
                print(cmd)
                run_command(cmd)
                cmd = f"e2fsdroid.exe -e -T 1230768000 -C {fsconfig_path} -S {filecontexts_path} -f {directoryname} -a /{part_name} {WorkDir}/output/{part_name}.img"
                run_command(cmd)
                print("Сборка завершена")
    else:
        print("Пожалуйста, выберите рабочую  папку")


def repack_erofs():
    if WorkDir:
        directoryname = askdirectory(title="Выберите раздел, который хотите собрать, например : .\\NH4_test\\vendor\\vendor")
        filecontexts_path, fsconfig_path = find_fs_con(directoryname)
        with cartoon():
            mkdir(WorkDir + os.sep + 'output')
            fspatch.main(directoryname, fsconfig_path)
            cmd = "mkfs.erofs.exe %s/output/%s.img %s -z\"%s\" -T\"1230768000\" --mount-point=/%s --fs-config-file=%s --file-contexts=%s" % (
                WorkDir, os.path.basename(directoryname), directoryname.replace("\\", "/"),
                settings.erofstype, os.path.basename(directoryname), fsconfig_path, filecontexts_path)
            print(cmd)
            run_command(cmd)
    else:
        print("Пожалуйста, выберите рабочую  папку")


def repack_dtbo():
    if WorkDir:
        directoryname = askdirectory(title="Выберите папку dtbo")
        if not os.path.isdir(WorkDir + os.sep + "output"):
            mkdir(WorkDir + os.sep + "output")
        cmd = "mkdtboimg.exe create %s\\output\\dtbo.img " % WorkDir
        for i in range(len([i for i in os.listdir(directoryname)])):
            cmd += "%s\\dtb.%s " % (directoryname, i)
        run_command(cmd)
        print("Сборка завершена")
    else:
        print("Пожалуйста,  выберите рабочую  папку")


def repack_sparse_image():
    if WorkDir:
        img_file_path = askopenfilename(title="Выберите файл IMG для преобразования в SIMG.")
        if not os.path.exists(img_file_path):
            print("Файл не найден: " + img_file_path)
        elif gettype(img_file_path) != "ext":
            print("Выбранный файл не является образом EXT, сначала преобразуйте его")
            return
        else:
            print("Преобразование")
            with cartoon():
                cmd = "img2simg %s %s/output/%s_sparse.img" % (
                    img_file_path, WorkDir, os.path.basename(img_file_path.replace('.img', '')))
                run_command(cmd)
                print("Преобразование завершено")
    else:
        print("Пожалуйста,  выберите рабочую  папку")


def compress_to_br():
    if WorkDir:
        img_file_path = askopenfilename(title="Выберите файл DAT, который вы хотите преобразовать в BR")
        if not os.path.exists(img_file_path):
            print("Файл не найден: " + img_file_path)
        elif gettype(img_file_path) != "dat":
            print("Выбранный файл не является DAT, пожалуйста, сначала преобразуйте его")
            return
        else:
            print("Преобразование")
            with cartoon():
                cz(run_command, "brotli.exe -q 6 " + img_file_path)
            print("После завершения преобразования перейдите рабочую  папку")
    else:
        print("Пожалуйста,  выберите рабочую  папку")


def repack_dat():
    if WorkDir:
        img_file_path = askopenfilename(title="Выберите файл IMG для преобразования в формат DAT")
        if not os.path.exists(img_file_path):
            print("Файл не найден: " + img_file_path)
        elif gettype(img_file_path) != "sparse":
            print("Выбранный файл не является SPARSE, пожалуйста, сначала преобразуйте его")
            return
        else:
            print("Предупреждение: Принимается ввод только основной версии, например, 7.1.2 Пожалуйста, введите 7.1!")
            input_version = float(user_input_window("Введите версию Android"))
            current_version = 0
            if input_version == 5.0:  # Android 5
                print("Выбрать: Android 5.0")
                current_version = 1
            elif input_version == 5.1:  # Android 5.1
                print("Выбрать: Android 5.1")
                current_version = 2
            elif 6.0 <= input_version < 7.0:  # Android 6.X
                print("Выбрать: Android 6.X")
                current_version = 3
            elif input_version >= 7.0:  # Android 7.0+
                print("Выбрать: Android 7.X+")
                current_version = 4
            print("Совет: Введите название раздела (например,system、vendor、odm)")
            partition_name = user_input_window("Введите название раздела")
            if current_version == 0:
                print("Версия Android введена неправильно, пожалуйста, проверьте подсказки для повторного ввода!")
                return
            elif partition_name == 0 or not partition_name:
                print("Название раздела введено неверно, проверьте подсказки и введите заново!")
                return
            print("Начать преобразование")
            with cartoon():
                cz(img2sdat.main, img_file_path, WorkDir + "/output/", current_version, partition_name)
            print("После завершения преобразования, перейдите в папку сохранения файла в рабочей папке")
    else:
        print("Пожалуйста,  выберите рабочую  папку")


def repack_dtb():
    if WorkDir:
        filename = askopenfilename(title="Выберите файл dts и поместите его в папку dtb.")
        if os.access(filename, os.F_OK):
            if not os.path.isdir(WorkDir + os.sep + "dtb"):
                mkdir(WorkDir + os.sep + "dtb")
            with cartoon():
                run_command("dtc -I dts -O dtb %s -o %s\\dtb\\%s.dtb" % (
                    filename, WorkDir, os.path.basename(filename).replace(".dts", ".dtb")))
            print("Преобразование в dtb завершено")
        else:
            print("Файл не найден")
    else:
        print("Пожалуйста,  выберите рабочую  папку")


def repack_super():
    if WorkDir:
        packtype = StringVar(value='VAB')
        packsize = StringVar(value="9126805504")
        packgroup = StringVar(value='main')
        img_dir = StringVar()
        sparse = IntVar()
        w = Toplevel()
        cur_width = 400
        cur_hight = 450
        size_xy = '%dx%d' % (cur_width, cur_hight)
        w.geometry(size_xy)
        w.resizable(False, False)
        w.title("Собрать Super")
        l1 = ttk.LabelFrame(w, text="Тип раздела", labelanchor="nw", relief=GROOVE, borderwidth=1)
        ttk.Radiobutton(l1, variable=packtype, value='VAB', text='VAB').pack(side=LEFT, expand=YES, padx=5)
        ttk.Radiobutton(l1, variable=packtype, value='AB', text='AB').pack(side=LEFT, expand=YES, padx=5)
        ttk.Radiobutton(l1, variable=packtype, value='A-only', text='A-only').pack(side=LEFT, expand=YES, padx=5)
        l1.pack(side=TOP, ipadx=10, ipady=10)
        ttk.Label(w, text="Размер супер раздела (в байтах) 9126805504)").pack(side=TOP)
        ttk.Entry(w, textvariable=packsize, width=50).pack(side=TOP, padx=10, pady=10, expand=YES, fill=BOTH)
        ttk.Label(w, text="Название разделов super образа").pack()
        ttk.Entry(w, textvariable=packgroup, width=50).pack(side=TOP, padx=10, pady=10, expand=YES, fill=BOTH)
        l2 = ttk.Labelframe(w, text="Папка с образом:", labelanchor="nw", relief=GROOVE, borderwidth=1)
        ttk.Entry(l2, textvariable=img_dir, width=50).pack(padx=10, pady=10, fill=X)
        ttk.Button(l2, text="Обзор",
                   command=lambda: img_dir.set(askdirectory(title="Выберите папку, в которой находится файл образа супер раздела"))).pack()
        l2.pack(ipadx=10, ipady=10)
        Checkbutton(w, text="Sparse", variable=sparse).pack(side=TOP, padx=10, pady=10)
        Button(w, text="Собрать", command=w.destroy, width=20, height=20).pack(padx=10, pady=10)
        w.wait_window()
        if not packtype.get():
            print("没有获取到选项")
        else:
            superdir = img_dir.get()
            if not superdir or not os.path.join(superdir):
                print("Папка не существует")
                return
            print("Папка, в которой находится super образ：" + superdir)
            if sparse.get():
                print("Преобразование в sparse образ")
            cmd = "lpmake "
            print("Тип упаковки ： " + packtype.get())
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
            run_command(cmd)
            print("Super собран успешно") if os.path.join(WorkDir, 'super.img') else print("Сборка super образа завершилась неудачей")

    else:
        print("Пожалуйста,  выберите рабочую  папку")


def setting():
    window = Toplevel()
    window.title("Настройки")
    screenwidth = window.winfo_screenwidth()
    screenheight = window.winfo_screenheight()
    window.geometry(
        '{}x{}+{}+{}'.format(600, 400, int(screenwidth / 2), int(screenheight / 2)))
    area1 = ttk.LabelFrame(window, text="Настройки Ext4")
    area1_label = ttk.Frame(area1)
    ttk.Label(area1_label, text="Автоматическое изменение размера:").pack(side=LEFT)
    zdtzdx = BooleanVar(value=settings.automutiimgsize)
    Checkbutton(area1_label, onvalue=True, offvalue=False, variable=zdtzdx,
                command=lambda: settings.change("automutiimgsize", zdtzdx.get())).pack(padx=10, pady=10, side=LEFT)
    area1_label.pack(fill=X)
    area1_custom_size = ttk.Frame(area1)
    ttk.Label(area1_custom_size, text="Размер EXT4 по умолчанию:").pack(side=LEFT)
    num_value = StringVar(value=settings.modifiedimgsize)
    Entry(area1_custom_size, textvariable=num_value).pack(padx=10, pady=10, side=LEFT)
    Button(area1_custom_size, text="Применить", command=lambda: settings.change('modifiedimgsize',
                                                                           num_value.get() if num_value.get().isdigit() else settings.modifiedimgsize)).pack(
        padx=10, pady=10, side=LEFT)
    area1_custom_size.pack(fill=X)
    area1_custom_type = ttk.Frame(area1)
    type_value = StringVar(value=settings.extrepacktype)
    ttk.Label(area1_custom_type, text="Способ упаковки MKE2FS:").pack(side=LEFT)
    Entry(area1_custom_type, textvariable=type_value).pack(padx=10, pady=10, side=LEFT)
    Button(area1_custom_type, text="Применить", command=lambda: settings.change('extrepacktype', type_value.get())).pack(
        padx=10, pady=10, side=LEFT)
    area1_custom_type.pack(fill=X)
    area1_block_size = ttk.Frame(area1)
    ttk.Label(area1_block_size, text="Размер блока:").pack(side=LEFT)
    block_size = StringVar(value=settings.extblocksize)
    Entry(area1_block_size, textvariable=block_size).pack(padx=10, pady=10, side=LEFT)
    Button(area1_block_size, text="Применить", command=lambda: settings.change('extblocksize',
                                                                          block_size.get() if block_size.get().isdigit() else settings.extblocksize)).pack(
        padx=10, pady=10, side=LEFT)
    area1_block_size.pack(fill=X)
    area1.pack(fill=BOTH, padx=10, pady=10)
    area2 = ttk.LabelFrame(window, text="Настройки EROFS")
    area2_type = ttk.Frame(area2)
    erofs_type = StringVar(value=settings.erofstype)
    ttk.Label(area2_type, text="Тип сжатия:").pack(side=LEFT, padx=10, pady=10)
    ttk.Entry(area2_type, textvariable=erofs_type).pack(side=LEFT)
    Button(area2_type, text="Применить", command=lambda: settings.change('erofstype', erofs_type.get())).pack(
        padx=10, pady=10, side=LEFT)
    area2_type.pack(fill=X)
    area2.pack(fill=BOTH, padx=10, pady=10)


class Mystdout:
    def __init__(self, master):
        sys.stdout = self
        sys.stderr = self
        self.master = master

    def write(self, info):
        self.master.configure(state='normal')
        if info not in ['\r', '\n', '\r\n']:
            self.master.insert(END, f"[{time.strftime('%H:%M:%S')}]{info}\n")
        self.master.update()
        self.master.yview('end')
        self.master.configure(state='disabled')

    def flush(self):
        ...


class App:
    def __init__(self):
        root = Style(theme=settings.theme).master
        global D
        D = PhotoImage(file="bin\\processdone.png")
        screenwidth = root.winfo_screenwidth()
        screenheight = root.winfo_screenheight()
        width = 1240
        height = 600
        if os.name != 'nt':
            root.geometry("%sx%s" % (width, height))
        root.title("NH4RomTool")
        root.geometry(
            '{}x{}+{}+{}'.format(width, height, int((screenwidth - width) / 2), int((screenheight - height) / 2)))
        menu_bar = Menu(root)
        root.config(menu=menu_bar)
        menu1 = Menu(menu_bar, tearoff=False)
        menu1.add_command(label="Настройки", command=setting)
        menu1.add_command(label="О программе", command=about)
        menu1.add_command(label="Выход", command=sys.exit)
        menu_bar.add_cascade(label="Меню", menu=menu1)
        menu2 = Menu(menu_bar, tearoff=False)
        menu_item = ["cosmo", "flatly", "journal", "literal", "lumen", "minty", "pulse", "sandstone", "united", "yeti",
                     "cyborg", "darkly", "solar", "vapor", "superhero"]
        for item in menu_item:
            menu2.add_command(label=item, command=lambda n=item: change_theme(n))
        menu_bar.add_cascade(label="Тема", menu=menu2)
        frame = ttk.LabelFrame(root, text="NH4 Rom Tool", labelanchor="nw", relief=GROOVE, borderwidth=1)
        frame1 = ttk.LabelFrame(frame, text="Функциональная зона", labelanchor="nw", relief=SUNKEN, borderwidth=1)
        frame2 = ttk.LabelFrame(frame, text="Логи", labelanchor="nw", relief=SUNKEN, borderwidth=1)
        tab_control = ttk.Notebook(frame1)
        tab1 = ttk.Frame(tab_control)
        tab2 = ttk.Frame(tab_control)
        tab3 = ttk.Frame(tab_control)
        tab33 = ScrolledFrame(tab3, autohide=True, width=220)
        tab_control.add(tab1, text="Проекты")
        tab_control.add(tab2, text="Упаковка и распаковка")
        tab_control.add(tab3, text="Другое")
        tab33.pack(side=LEFT, expand=YES, fill=BOTH)
        tab11 = ttk.Frame(tab1)
        self.table = ttk.Treeview(tab11, height=10, columns=["Workdir"], show='headings')
        self.table.column('Workdir', width=100, anchor='center')
        self.table.heading('Workdir', text='Список проектов')
        self.table.pack(side=TOP, fill=BOTH, expand=YES)
        self.table.bind('<ButtonRelease-1>', lambda *x_: self.select_work_dir())
        self.get_work_dir()
        tab12 = ttk.Frame(tab1)
        ttk.Button(tab12, text='Выбрать', width=10,
                   command=lambda: tab_control.select(tab2) if WorkDir else print("Пожалуйста, выберите файл"),
                   style='primiary.Outline.TButton').grid(row=0,
                                                          column=0,
                                                          padx=10,
                                                          pady=8)
        ttk.Button(tab12, text='Удалить', width=10, command=self.rm_work_dir, style='primiary.Outline.TButton').grid(row=0,
                                                                                                                  column=1,
                                                                                                                  padx=10,
                                                                                                                  pady=8)
        ttk.Button(tab12, text='Создать', width=10,
                   command=lambda: (mkdir(f'NH4_{user_input_window()}') or self.get_work_dir()),
                   style='primiary.Outline.TButton').grid(row=1,
                                                          column=0,
                                                          padx=10,
                                                          pady=8)
        ttk.Button(tab12, text='Обновить', width=10, command=self.get_work_dir, style='primiary.Outline.TButton').grid(
            row=1,
            column=1,
            padx=10,
            pady=8)
        ttk.Button(tab12, text='Очистить', width=10, command=clear_work_dir, style='primiary.Outline.TButton').grid(row=2,
                                                                                                                column=0,
                                                                                                                padx=10,
                                                                                                                pady=8)
        tab12.pack(side=BOTTOM, fill=BOTH, expand=YES, anchor=CENTER)
        tab_control.pack(fill=BOTH, expand=YES)
        tab11.pack(side=TOP, fill=BOTH, expand=YES)
        tab21 = ttk.LabelFrame(tab2, text="Распаковка", labelanchor="nw", relief=SUNKEN, borderwidth=1)
        ttk.Button(tab21, text='ИзвлечьZip', width=10, command=lambda: cz(unzip), style='primiary.Outline.TButton').grid(
            row=0, column=0,
            padx=10,
            pady=8)
        ttk.Button(tab21, text='Разобрать', width=10, command=lambda: cz(smart_unpack),
                   style='primiary.Outline.TButton').grid(row=0,
                                                          column=1,
                                                          padx=10,
                                                          pady=8)
        tab22 = ttk.LabelFrame(tab2, text="Упаковка", labelanchor="nw", relief=SUNKEN, borderwidth=1)
        ttk.Button(tab22, text='СобратьZip', width=10, command=lambda: cz(zip_compress),
                   style='primiary.Outline.TButton').grid(row=0,
                                                          column=0,
                                                          padx=10,
                                                          pady=8)
        ttk.Button(tab22, text='BOOT', width=10, command=repackboot, style='primiary.Outline.TButton').grid(row=0,
                                                                                                            column=1,
                                                                                                            padx=10,
                                                                                                            pady=8)
        ttk.Button(tab22, text='EXT', width=10, command=lambda: cz(repack_ext),
                   style='primiary.Outline.TButton').grid(row=1,
                                                          column=0,
                                                          padx=10,
                                                          pady=8)
        ttk.Button(tab22, text='EROFS', width=10, command=lambda: cz(repack_erofs),
                   style='primiary.Outline.TButton').grid(row=1,
                                                          column=1,
                                                          padx=10,
                                                          pady=8)
        ttk.Button(tab22, text='DTS2DTB', width=10, command=lambda: cz(repack_dtb),
                   style='primiary.Outline.TButton').grid(
            row=2,
            column=0,
            padx=10,
            pady=8)
        ttk.Button(tab22, text='DTBO', width=10, command=lambda: cz(repack_dtbo),
                   style='primiary.Outline.TButton').grid(
            row=2, column=1,
            padx=10,
            pady=8)
        ttk.Button(tab22, text='SUPER', width=10, command=lambda: cz(repack_super),
                   style='primiary.Outline.TButton').grid(
            row=3,
            column=0,
            padx=10,
            pady=8)
        ttk.Button(tab22, text='EXT->SIMG', width=10, command=lambda: cz(repack_sparse_image),
                   style='primiary.Outline.TButton').grid(
            row=3, column=1, padx=10, pady=8)
        ttk.Button(tab22, text='IMG->DAT', width=10, command=lambda: cz(repack_dat),
                   style='primiary.Outline.TButton').grid(row=4,
                                                          column=0,
                                                          padx=10,
                                                          pady=8)
        ttk.Button(tab22, text='DAT->BR', width=10, command=lambda: cz(compress_to_br),
                   style='primiary.Outline.TButton').grid(row=4,
                                                          column=1,
                                                          padx=10,
                                                          pady=8)
        tab21.pack(side=TOP, fill=BOTH)
        tab22.pack(side=TOP, fill=BOTH, expand=YES)
        for t, c in (("Определение формата файла", lambda: print(
                f"Формат файла : {gettype(filename)}" if os.access((filename := askopenfilename(title="Определение типа файла")),
                                                                 os.F_OK) else "Error : Файл не найден")), ('Расшифровать OZIP',
                                                                                                        lambda: ozip_decrypt.main(
                                                                                                            filename) if os.access(
                                                                                                            (
                                                                                                                    filename := askopenfilename(
                                                                                                                        title="Расшифровка ozip")),
                                                                                                            os.F_OK) else print(
                                                                                                            "Error : Файл не найден")),
                     ('Зашифровать OZIP', lambda: cz(ozip_encrypt)), ('Отключить проверку VBMETA', patch_vbmeta),
                     ('Исправление FS_CONFIG', lambda: cz(fspatch.main, askdirectory(title="Выберите папку, в которой находится файл"),
                                                        askopenfilename(title="Выберите файл fs_config"))),):
            ttk.Button(tab33, text=t, width=10, command=c, bootstyle="link").pack(
                side=TOP, expand=NO,
                fill=X, padx=8)
        self.text = scrolledtext.ScrolledText(frame2, width=180, height=18, font=['Arial', 10], relief=SOLID)
        self.text.pack(side=TOP, expand=YES, fill=BOTH, padx=4, pady=2)
        Mystdout(self.text)
        frame22 = ttk.LabelFrame(frame2, text="Введите пользовательскую команду", labelanchor="nw", relief=SUNKEN, borderwidth=1)

        def run_cmd():
            cmd = usercmd.get()
            if cmd:
                cz(run_command, f'busybox ash -c "{cmd}"')
            usercmd.delete(0, 'end')

        usercmd = ttk.Entry(frame22, width=25)
        usercmd.pack(side=LEFT, expand=YES, fill=X, padx=2, pady=2)
        usercmd.bind('<Return>', lambda *x: run_cmd())
        ttk.Button(frame22, text='Старт', command=run_cmd, style='primary.Outline.TButton').pack(side=LEFT, expand=NO,
                                                                                                fill=X, padx=2, pady=2)
        frame.pack(side=TOP, expand=YES, fill=BOTH, padx=2, pady=2)
        frame1.pack(side=LEFT, expand=YES, fill=BOTH, padx=5, pady=2)
        frame2.pack(side=LEFT, expand=YES, fill=BOTH, padx=5, pady=2)
        frame22.pack(side=TOP, expand=NO, fill=BOTH, padx=5, pady=2)
        frame_bottom = ttk.Frame(root, relief=FLAT, borderwidth=0)

        def clean():
            self.text.configure(state='normal')
            self.text.delete(1.0, END)
            self.text.configure(state='disabled')

        ttk.Button(frame_bottom, text='Очистить', command=clean, style='secondary.TButton').pack(side=RIGHT, padx=5, pady=0)
        global statusbar
        statusbar = ttk.Label(frame_bottom, relief='flat', anchor=E, image=D, bootstyle="info")
        statusbar.pack(side=RIGHT, fill=X, ipadx=12)

        def show_poem():
            shiju = requests_get("https://v1.jinrishici.com/all", proxies={"http": None,
                                                                           "https": None}).json()
            ttk.Label(frame_bottom, text="%s —— %s  《%s》" % (shiju['content'], shiju['author'], shiju['origin']),
                      font=('微软雅黑', 12)).pack(side=LEFT, padx=8)

        cz(show_poem)
        frame_bottom.pack(side=BOTTOM, expand=NO, fill=X, padx=8, pady=12)
        cz(root.iconbitmap, "bin\\logo.ico")
        root.mainloop()

    def get_work_dir(self):
        [self.table.delete(i) for i in self.table.get_children()]
        [self.table.insert('', 'end', value=i) for i in
         os.listdir(LOCALDIR)
         if i.startswith('NH4')]

    def select_work_dir(self):
        if not self.table.selection():
            return
        item_text = self.table.item(self.table.selection()[0], "values")
        if item_text[0]:
            global WorkDir
            WorkDir = item_text[0]
            print(f"Выберите рабочую папку: {WorkDir}")

    def rm_work_dir(self):
        if WorkDir:
            print(f"Удаление папки: {WorkDir}")
            shutil.rmtree(WorkDir)
        else:
            print("Error : Папка, которую вы хотите удалить, не существует")
        self.get_work_dir()


if __name__ == '__main__':
    App()
