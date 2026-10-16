import sqlite3,json
from datetime import datetime
DB='stylist.db'
def init():
    with sqlite3.connect(DB) as c:
        c.execute('CREATE TABLE IF NOT EXISTS interactions (id INTEGER PRIMARY KEY, occasion TEXT, style TEXT, budget REAL, total REAL, created_at TEXT)')
        c.execute('CREATE TABLE IF NOT EXISTS favorites (id INTEGER PRIMARY KEY, product_ids TEXT, explanation TEXT, created_at TEXT)')
def record(occasion,style,budget,total):
    with sqlite3.connect(DB) as c: c.execute('INSERT INTO interactions (occasion,style,budget,total,created_at) VALUES (?,?,?,?,?)',(occasion,style,budget,total,datetime.now().isoformat()))
def favorite(ids,explanation):
    with sqlite3.connect(DB) as c: c.execute('INSERT INTO favorites (product_ids,explanation,created_at) VALUES (?,?,?)',(json.dumps(ids),explanation,datetime.now().isoformat()))
def favorites():
    with sqlite3.connect(DB) as c: return c.execute('SELECT product_ids,explanation,created_at FROM favorites ORDER BY id DESC').fetchall()
def analytics():
    with sqlite3.connect(DB) as c:
        totals=c.execute('SELECT COUNT(*),AVG(total),AVG(budget) FROM interactions').fetchone()
        styles=c.execute('SELECT style,COUNT(*) FROM interactions GROUP BY style ORDER BY COUNT(*) DESC').fetchall()
        occasions=c.execute('SELECT occasion,COUNT(*) FROM interactions GROUP BY occasion ORDER BY COUNT(*) DESC').fetchall()
    return totals,styles,occasions
