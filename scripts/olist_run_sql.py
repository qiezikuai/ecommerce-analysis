# -*- coding: utf-8 -*-
"""运行 sql/olist/ 下的分析 SQL 并打印结果。
用法: python scripts/olist_run_sql.py [文件名]   # 不传则运行全部(跳过 01_建表)
"""
import os, sys, glob
import pymysql

sys.stdout.reconfigure(encoding="utf-8")
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
sql_dir = os.path.join(base, "..", "sql", "olist")

if len(sys.argv) > 1:
    files = [os.path.join(sql_dir, sys.argv[1])]
else:
    files = sorted(glob.glob(os.path.join(sql_dir, "*.sql")))
    files = [f for f in files if not os.path.basename(f).startswith("01_")]

conn = pymysql.connect(host=cfg["host"], port=int(cfg["port"]), user=cfg["user"],
                       password=cfg["password"], database=cfg["database"], charset="utf8mb4")
for f in files:
    print("\n" + "=" * 70)
    print("FILE:", os.path.basename(f))
    print("=" * 70)
    with conn.cursor() as cur:
        sql = open(f, encoding="utf-8-sig").read()
        for stmt in [s.strip() for s in sql.split(";") if s.strip()]:
            try:
                cur.execute(stmt)
            except Exception as e:
                print("!! 语句失败:", e)
                print("  语句前 100 字:", stmt[:100].replace("\n", " "))
                continue
            if cur.description:
                cols = [d[0] for d in cur.description]
                rows = cur.fetchall()
                print(" | ".join(str(c) for c in cols))
                for r in rows:
                    print(" | ".join(str(x) for x in r))
                print("(%d 行)" % len(rows))
            else:
                print("(执行成功, 影响 %d 行)" % cur.rowcount)
conn.close()
print("\n全部完成")
