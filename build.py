import os
import platform
import shutil
import zipfile

print(f'Build for {platform.system()}')
from pip._internal.cli.main import main as _main

with open('requirements.txt', 'r', encoding='utf-8') as l:
    for i in l.read().split("\n"):
        print(f"Installing {i}")
        _main(['install', i])
local = os.getcwd()
name = 'NH4RomTool-win.zip'


def zip_folder(folder_path):
    # 获取文件夹的绝对路径和文件夹名称
    abs_folder_path = os.path.abspath(folder_path)

    # 创建一个同名的zip文件
    zip_file_path = os.path.join(local, name)
    archive = zipfile.ZipFile(zip_file_path, "w", zipfile.ZIP_DEFLATED)

    # 遍历文件夹中的所有文件和子文件夹
    for root, dirs, files in os.walk(abs_folder_path):
        for file in files:
            if file == name:
                continue
            file_path = os.path.join(root, file)
            if ".git" in file_path:
                continue
            print(f"Adding: {file_path}")
            # 将文件添加到zip文件中
            archive.write(file_path, os.path.relpath(file_path, abs_folder_path))

    # 关闭zip文件
    archive.close()
    print(f"Done!")


import PyInstaller.__main__

PyInstaller.__main__.run(['-F', 'ui.py', '--exclude-module=numpy', '-i', 'icon.ico'])

if os.name == 'nt':
    if os.path.exists(local + os.sep + "dist" + os.sep + "ui.exe"):
        shutil.move(local + os.sep + "dist" + os.sep + "ui.exe", local)

for i in os.listdir(local):
    if i not in ['run', 'ui.exe', 'bin', 'LICENSE']:
        print(f"Removing {i}")
        if os.path.isdir(local + os.sep + i):
            try:
                shutil.rmtree(local + os.sep + i)
            except Exception or OSError as e:
                print(e)
        elif os.path.isfile(local + os.sep + i):
            try:
                os.remove(local + os.sep + i)
            except Exception or OSError as e:
                print(e)
    else:
        print(i)

zip_folder(".")
