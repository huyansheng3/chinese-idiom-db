#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import hashlib
from PIL import Image
import io
import shutil
from collections import defaultdict

def calculate_image_hash(image_path):
    """
    计算图片的哈希值，用于判断图片是否重复
    
    参数:
        image_path: 图片路径
    返回:
        图片的MD5哈希值
    """
    try:
        # 打开图片并调整大小以加快处理速度
        with Image.open(image_path) as img:
            # 调整图片大小为缩略图，保持比例
            img.thumbnail((100, 100))
            # 转换为字节流
            buffer = io.BytesIO()
            img.save(buffer, format=img.format or 'JPEG')
            # 计算哈希值
            return hashlib.md5(buffer.getvalue()).hexdigest()
    except Exception as e:
        print(f"处理图片 {image_path} 时出错: {e}")
        return None

def find_duplicate_images(root_dir='chengyu_images'):
    """
    查找成语图片目录下的所有重复图片
    
    参数:
        root_dir: 成语图片的根目录
    返回:
        重复图片的字典，键为图片哈希值，值为图片路径列表
    """
    if not os.path.exists(root_dir):
        print(f"目录 {root_dir} 不存在")
        return {}
    
    # 用于存储图片哈希值和路径
    hash_dict = defaultdict(list)
    total_images = 0
    
    # 遍历所有成语目录
    for chengyu_dir in os.listdir(root_dir):
        dir_path = os.path.join(root_dir, chengyu_dir)
        
        # 跳过非目录文件
        if not os.path.isdir(dir_path):
            continue
            
        # 遍历目录中的所有文件
        for file in os.listdir(dir_path):
            file_path = os.path.join(dir_path, file)
            
            # 如果是图片文件，则计算哈希值
            if os.path.isfile(file_path) and file.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.bmp')):
                total_images += 1
                img_hash = calculate_image_hash(file_path)
                if img_hash:
                    hash_dict[img_hash].append(file_path)
    
    # 筛选出有重复的图片
    duplicates = {h: paths for h, paths in hash_dict.items() if len(paths) > 1}
    
    print(f"共扫描了 {total_images} 张图片")
    print(f"发现 {len(duplicates)} 组重复图片，共 {sum(len(p) for p in duplicates.values())} 张")
    
    return duplicates

def remove_duplicates(duplicates, keep_first=True):
    """
    删除重复的图片
    
    参数:
        duplicates: 重复图片的字典，键为图片哈希值，值为图片路径列表
        keep_first: 是否保留每组重复图片中的第一张
    """
    removed_count = 0
    
    for img_hash, paths in duplicates.items():
        # 决定要保留的图片
        if keep_first:
            # 按照成语名称排序，优先保留字母序靠前的成语目录中的图片
            paths.sort()
            keep_path = paths[0]
            remove_paths = paths[1:]
        else:
            # 全部删除
            keep_path = None
            remove_paths = paths
        
        # 输出信息
        if keep_path:
            print(f"\n保留: {keep_path}")
        
        # 删除重复图片
        for path in remove_paths:
            try:
                os.remove(path)
                print(f"删除: {path}")
                removed_count += 1
            except Exception as e:
                print(f"删除 {path} 时出错: {e}")
    
    print(f"\n共删除了 {removed_count} 张重复图片")

def confirm_deletion():
    """确认用户是否真的要删除重复图片"""
    response = input("警告：此操作将删除 chengyu_images 目录下的重复图片！确定要继续吗？(y/n): ")
    return response.lower() in ('y', 'yes')

if __name__ == "__main__":
    # 可以通过命令行参数指定目录
    root_dir = sys.argv[1] if len(sys.argv) > 1 else 'chengyu_images'
    
    print(f"正在扫描 {root_dir} 目录中的图片...")
    duplicates = find_duplicate_images(root_dir)
    
    if duplicates:
        if confirm_deletion():
            remove_duplicates(duplicates, keep_first=True)
        else:
            print("操作已取消")
    else:
        print("未发现重复图片") 