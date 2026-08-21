# -*- coding: utf-8 -*-
"""运行 sql/ 下的 .sql 文件并打印结果。
用法（项目根目录下）: python scripts/run_sql.py sql/02_整体转化漏斗.sql
"""
import os, sys
import pymysql

# 中文输出兼容：在 UTF-8 终端(Windows Terminal/VSCode)下正常显示；乱码就先执行 chcp 65001
try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

base = os.path.dirname(os.path.abspath(__file__))

def load_env(path):
    d = {}
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or "=" not in line:
                continue
            k, v = line.split("=", 1)
            d[k.strip()] = v.strip()
    return d

cfg = load_env(os.path.join(base, "..", "config", "db.env"))
if len(sys.argv) < 2:
    print("用法: python scripts/run_sql.py <sql 文件路径>")
    sys.exit(1)

sql_path = os.path.join(base, "..", sys.argv[1])
if not os.path.exists(sql_path):
    print("文件不存在:", sql_path)
    sys.exit(1)

conn = pymysql.connect(host=cfg["host"], port=int(cfg["port"]), user=cfg["user"],
                       password=cfg["password"], database=cfg["database"], charset="utf8mb4")
with conn.cursor() as cur:
    with open(sql_path, encoding="utf-8-sig") as f:
        statements = [s.strip() for s in f.read().split(";") if s.strip()]
    for stmt in statements:
        print(">>>", stmt.splitlines()[0][:70])
        cur.execute(stmt)
        if cur.description:
            cols = [d[0] for d in cur.description]
            rows = cur.fetchall()
            print(" | ".join(cols))
            for row in rows:
                print(" | ".join(str(x) for x in row))
            print("(%d 行)" % len(rows))
        else:
            print("(执行成功, 影响 %d 行)" % cur.rowcount)
conn.close()