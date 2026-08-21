# -*- coding: utf-8 -*-
"""本地初始化 MySQL：创建 ecommerce 库 + analyst 专用账号，凭据写入 config/db.env（已 git 忽略）。
用法：在项目目录运行  python scripts/setup_mysql.py
安全说明：root 密码仅在本机输入，不会写入任何文件或日志。"""
import os, secrets, string, getpass

try:
    import pymysql
except ImportError:
    print("缺少 pymysql，请先运行: python -m pip install pymysql")
    raise SystemExit(1)

root_pwd = getpass.getpass("请输入 MySQL root 密码（输入时不显示，回车确认）: ")
analyst_pwd = "".join(secrets.choice(string.ascii_letters + string.digits) for _ in range(16))

try:
    conn = pymysql.connect(host="127.0.0.1", port=3306, user="root", password=root_pwd)
except Exception as e:
    print("连接失败，请检查密码/服务是否在运行：", e)
    raise SystemExit(1)

try:
    with conn.cursor() as cur:
        cur.execute("CREATE DATABASE IF NOT EXISTS ecommerce DEFAULT CHARACTER SET utf8mb4")
        cur.execute("CREATE USER IF NOT EXISTS 'analyst'@'localhost' IDENTIFIED BY %s", (analyst_pwd,))
        cur.execute("ALTER USER 'analyst'@'localhost' IDENTIFIED BY %s", (analyst_pwd,))
        cur.execute("GRANT ALL PRIVILEGES ON ecommerce.* TO 'analyst'@'localhost'")
        cur.execute("FLUSH PRIVILEGES")
    conn.commit()
finally:
    conn.close()

base = os.path.dirname(os.path.abspath(__file__))
cfg_dir = os.path.join(base, "..", "config")
os.makedirs(cfg_dir, exist_ok=True)
env_file = os.path.join(cfg_dir, "db.env")
with open(env_file, "w", encoding="utf-8") as f:
    f.write("host=127.0.0.1\nport=3306\nuser=analyst\npassword=%s\ndatabase=ecommerce\n" % analyst_pwd)

gitignore = os.path.join(base, "..", ".gitignore")
with open(gitignore, "a", encoding="utf-8") as f:
    if "config/" not in open(gitignore, encoding="utf-8").read():
        f.write("\nconfig/\n")

print("完成：已创建库 ecommerce + 专用账号 analyst，凭据在 config/db.env（已加入 .gitignore）。")
print("数据库初始化完成。可运行 python scripts/import_to_mysql.py 导入数据。")
