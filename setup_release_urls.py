#!/usr/bin/env python3
"""
一次性設定腳本：把 READY 影片上傳到 GitHub Release，並將下載 URL 存入 DB。
執行前需先 gh auth login，並在 abide_system/ 目錄已建好 GitHub repo。

用法：python setup_release_urls.py --repo <owner/repo>
"""
import sys
import os
import json
import subprocess
import argparse
sys.path.insert(0, os.path.dirname(__file__))

from database import init_db, get_by_status, set_video_url

RELEASE_TAG = "v1-videos"

def run_gh(*args):
    result = subprocess.run(["gh"] + list(args), capture_output=True, text=True)
    if result.returncode != 0:
        print(f"❌ gh error: {result.stderr}")
        sys.exit(1)
    return result.stdout.strip()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True, help="owner/repo 格式，如 apple123/abide-upload")
    args = parser.parse_args()
    repo = args.repo

    init_db()
    rows = get_by_status("READY")

    # 建立 Release（若已存在則跳過）
    existing = subprocess.run(
        ["gh", "release", "view", RELEASE_TAG, "--repo", repo, "--json", "tagName"],
        capture_output=True, text=True
    )
    if existing.returncode != 0:
        print(f"📦 建立 GitHub Release {RELEASE_TAG}...")
        run_gh("release", "create", RELEASE_TAG,
               "--repo", repo,
               "--title", "Abide Videos",
               "--notes", "自動上傳用影片資產",
               "--latest=false")
    else:
        print(f"✅ Release {RELEASE_TAG} 已存在，跳過建立")

    # 取得現有 assets
    assets_json = run_gh("release", "view", RELEASE_TAG,
                         "--repo", repo, "--json", "assets")
    existing_assets = {a["name"]: a["url"] for a in json.loads(assets_json).get("assets", [])}

    updated = 0
    for row in rows:
        file_path = row["file_path"]
        filename = os.path.basename(file_path)

        if not os.path.exists(file_path):
            print(f"⚠️  跳過（找不到檔案）：{filename}")
            continue

        if filename in existing_assets:
            print(f"✅ 已存在，更新 URL：{filename}")
            download_url = f"https://github.com/{repo}/releases/download/{RELEASE_TAG}/{filename}"
            set_video_url(file_path, download_url)
            updated += 1
            continue

        print(f"⬆️  上傳：{filename}")
        run_gh("release", "upload", RELEASE_TAG, file_path, "--repo", repo)
        download_url = f"https://github.com/{repo}/releases/download/{RELEASE_TAG}/{filename}"
        set_video_url(file_path, download_url)
        print(f"   ✅ URL 已存入 DB")
        updated += 1

    print(f"\n完成！共更新 {updated} 支影片的 video_url")

if __name__ == "__main__":
    main()
