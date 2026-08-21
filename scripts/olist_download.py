# -*- coding: utf-8 -*-
"""下载 Olist 巴西电商真实公开数据集（kagglehub 匿名下载，无需注册）。
数据来源: https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce
下载到 data/olist/raw/"""
import os, shutil, sys
import kagglehub

sys.stdout.reconfigure(encoding="utf-8")
src = kagglehub.dataset_download("olistbr/brazilian-ecommerce")
dst = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "olist", "raw")
os.makedirs(dst, exist_ok=True)
for f in os.listdir(src):
    if f.endswith(".csv"):
        shutil.copy2(os.path.join(src, f), os.path.join(dst, f))
        print("copied:", f)
print("Olist raw data ready at:", dst)