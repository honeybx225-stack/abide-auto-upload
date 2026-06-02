#!/usr/bin/env python3
"""
每日自動上傳腳本
用法：python auto_upload.py [--dry-run]
"""
import sys
import os
import argparse
import socket
import time
import tempfile
import urllib.request
sys.path.insert(0, os.path.dirname(__file__))

from database import init_db, get_next_to_post, mark_uploaded
from meta_api import upload_reel
from datetime import datetime

def wait_for_network(host="graph.facebook.com", timeout=60):
    """等待網路就緒，最多等 timeout 秒"""
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            socket.getaddrinfo(host, 443)
            return True
        except socket.gaierror:
            time.sleep(5)
    return False

def download_video(url):
    """從 URL 下載影片到臨時檔案，回傳路徑"""
    tmp = tempfile.NamedTemporaryFile(suffix='.mp4', delete=False)
    tmp.close()
    print(f"  ⬇️ 下載影片...")
    urllib.request.urlretrieve(url, tmp.name)
    return tmp.name

def run(dry_run=False):
    if not dry_run:
        print("🌐 等待網路連線...")
        if not wait_for_network():
            print("❌ 網路無法連線，放棄上傳")
            return
        print("✅ 網路已就緒")

    init_db()
    row = get_next_to_post()

    if row is None:
        print("✅ 目前沒有待上傳的影片")
        return

    vol_num = row["vol_num"]
    short_num = row["short_num"]
    lang = row["lang"]
    file_path = row["file_path"]
    zh_caption = row["zh_caption"]
    en_caption = row["en_caption"]
    hashtags = row["hashtags"]
    post_title = row["post_title"]
    video_url = row["video_url"] if "video_url" in row.keys() else None

    caption_body = en_caption if lang == "EN" else zh_caption
    caption = f"{post_title}\n\n{caption_body}\n\n{hashtags}"

    print(f"📋 準備上傳：Vol.{vol_num} Short{short_num} [{lang}]")
    print(f"   標題：{post_title}")

    temp_file = None
    try:
        if os.path.exists(file_path):
            upload_path = file_path
        elif video_url:
            upload_path = download_video(video_url)
            temp_file = upload_path
        else:
            print(f"❌ 找不到檔案，也沒有 video_url：{file_path}")
            return

        if dry_run:
            print("   [Dry Run] 跳過實際上傳")
            return

        fb_id, ig_id = upload_reel(upload_path, caption)

        if fb_id or ig_id:
            now = datetime.now().isoformat()
            mark_uploaded(file_path, now, fb_post_id=fb_id, ig_post_id=ig_id)
            print(f"✅ 上傳完成 | FB: {fb_id} | IG: {ig_id}")
        else:
            print("❌ 上傳失敗，狀態未更新")
    finally:
        if temp_file and os.path.exists(temp_file):
            os.unlink(temp_file)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="模擬執行，不實際上傳")
    args = parser.parse_args()
    run(dry_run=args.dry_run)
