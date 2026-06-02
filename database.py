import sqlite3
from config import DB_PATH

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS shorts (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            vol_num     INTEGER NOT NULL,
            vol_name    TEXT NOT NULL,
            short_num   INTEGER NOT NULL,
            lang        TEXT NOT NULL,
            short_name  TEXT NOT NULL,
            file_path   TEXT UNIQUE NOT NULL,
            status      TEXT NOT NULL DEFAULT 'DRAFT',
            zh_caption  TEXT,
            en_caption  TEXT,
            hashtags    TEXT,
            post_title  TEXT,
            scheduled_dt TEXT,
            uploaded_dt TEXT,
            fb_post_id  TEXT,
            ig_post_id  TEXT,
            created_at  TEXT DEFAULT (datetime('now'))
        )
    """)
    try:
        conn.execute("ALTER TABLE shorts ADD COLUMN video_url TEXT")
    except Exception:
        pass
    conn.commit()
    conn.close()

def upsert_short(vol_num, vol_name, short_num, lang, short_name, file_path):
    conn = get_conn()
    conn.execute("""
        INSERT OR IGNORE INTO shorts
            (vol_num, vol_name, short_num, lang, short_name, file_path, status)
        VALUES (?, ?, ?, ?, ?, ?, 'DRAFT')
    """, (vol_num, vol_name, short_num, lang, short_name, file_path))
    conn.commit()
    conn.close()

def get_all():
    conn = get_conn()
    rows = conn.execute("""
        SELECT * FROM shorts
        ORDER BY vol_num, short_num, lang
    """).fetchall()
    conn.close()
    return rows

def get_by_status(status):
    conn = get_conn()
    rows = conn.execute("""
        SELECT * FROM shorts WHERE status = ?
        ORDER BY vol_num, short_num, lang
    """, (status,)).fetchall()
    conn.close()
    return rows

def get_next_to_post():
    conn = get_conn()
    row = conn.execute("""
        SELECT * FROM shorts
        WHERE status IN ('READY', 'DRAFT')
        AND (zh_caption IS NOT NULL OR en_caption IS NOT NULL)
        ORDER BY vol_num, short_num,
            CASE lang WHEN 'EN' THEN 0 WHEN 'ZH' THEN 1 ELSE 2 END
        LIMIT 1
    """).fetchone()
    conn.close()
    return row

def update_captions(file_path, zh_caption, en_caption, hashtags, post_title):
    conn = get_conn()
    conn.execute("""
        UPDATE shorts SET
            zh_caption = ?,
            en_caption = ?,
            hashtags   = ?,
            post_title = ?,
            status     = CASE WHEN status = 'DRAFT' THEN 'READY' ELSE status END
        WHERE file_path = ?
    """, (zh_caption, en_caption, hashtags, post_title, file_path))
    conn.commit()
    conn.close()

def update_status(file_path, status, scheduled_dt=None, uploaded_dt=None,
                  fb_post_id=None, ig_post_id=None):
    conn = get_conn()
    conn.execute("""
        UPDATE shorts SET
            status       = ?,
            scheduled_dt = COALESCE(?, scheduled_dt),
            uploaded_dt  = COALESCE(?, uploaded_dt),
            fb_post_id   = COALESCE(?, fb_post_id),
            ig_post_id   = COALESCE(?, ig_post_id)
        WHERE file_path = ?
    """, (status, scheduled_dt, uploaded_dt, fb_post_id, ig_post_id, file_path))
    conn.commit()
    conn.close()

def mark_uploaded(file_path, uploaded_dt, fb_post_id=None, ig_post_id=None):
    update_status(file_path, 'UPLOADED',
                  uploaded_dt=uploaded_dt,
                  fb_post_id=fb_post_id,
                  ig_post_id=ig_post_id)

def set_video_url(file_path, video_url):
    conn = get_conn()
    conn.execute("UPDATE shorts SET video_url = ? WHERE file_path = ?", (video_url, file_path))
    conn.commit()
    conn.close()
