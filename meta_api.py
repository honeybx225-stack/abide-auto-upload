"""
Meta Graph API — Facebook Reels + Instagram Reels 上傳
"""
import requests
import os
import time
from config import META_PAGE_ID, META_IG_ID, META_ACCESS_TOKEN

GRAPH = "https://graph.facebook.com/v19.0"

def _check_config():
    if not META_PAGE_ID or not META_ACCESS_TOKEN:
        raise ValueError("請先設定 META_PAGE_ID 和 META_ACCESS_TOKEN 環境變數")

# ─────────────────────────────────────────────
# Facebook Reels
# ─────────────────────────────────────────────

def upload_fb_reel(video_path, caption):
    _check_config()
    file_size = os.path.getsize(video_path)

    # Step 1: 初始化上傳
    r = requests.post(f"{GRAPH}/{META_PAGE_ID}/video_reels", data={
        "upload_phase": "start",
        "access_token": META_ACCESS_TOKEN,
    })
    r.raise_for_status()
    data = r.json()
    video_id = data["video_id"]
    upload_url = data["upload_url"]

    # Step 2: 上傳影片 bytes
    with open(video_path, "rb") as f:
        upload_r = requests.post(upload_url, headers={
            "Authorization": f"OAuth {META_ACCESS_TOKEN}",
            "offset": "0",
            "file_size": str(file_size),
        }, data=f)
        upload_r.raise_for_status()

    # Step 3: 發布
    pub_r = requests.post(f"{GRAPH}/{META_PAGE_ID}/video_reels", data={
        "upload_phase": "finish",
        "video_state": "PUBLISHED",
        "video_id": video_id,
        "description": caption,
        "access_token": META_ACCESS_TOKEN,
    })
    pub_r.raise_for_status()
    return video_id

# ─────────────────────────────────────────────
# Instagram Reels
# ─────────────────────────────────────────────

def upload_ig_reel(video_path, caption):
    _check_config()
    if not META_IG_ID:
        raise ValueError("請先設定 META_IG_ID 環境變數")

    file_size = os.path.getsize(video_path)

    # Step 1: 初始化 resumable upload container
    r = requests.post(f"{GRAPH}/{META_IG_ID}/media", params={
        "media_type": "REELS",
        "caption": caption,
        "share_to_feed": "true",
        "upload_type": "resumable",
        "access_token": META_ACCESS_TOKEN,
    })
    r.raise_for_status()
    data = r.json()
    container_id = data.get("id")
    upload_url = data.get("uri")

    if not container_id or not upload_url:
        raise ValueError(f"IG 初始化失敗: {data}")

    # Step 2: 上傳影片 bytes
    with open(video_path, "rb") as f:
        upload_r = requests.post(upload_url, headers={
            "Authorization": f"OAuth {META_ACCESS_TOKEN}",
            "offset": "0",
            "file_size": str(file_size),
        }, data=f)
        upload_r.raise_for_status()

    # Step 3: 等待處理完成
    for _ in range(20):
        time.sleep(10)
        status_r = requests.get(f"{GRAPH}/{container_id}", params={
            "fields": "status_code",
            "access_token": META_ACCESS_TOKEN,
        })
        status = status_r.json().get("status_code")
        if status == "FINISHED":
            break
        if status == "ERROR":
            raise ValueError("IG 影片處理失敗")

    # Step 4: 發布
    pub_r = requests.post(f"{GRAPH}/{META_IG_ID}/media_publish", params={
        "creation_id": container_id,
        "access_token": META_ACCESS_TOKEN,
    })
    pub_r.raise_for_status()
    return pub_r.json().get("id")


# ─────────────────────────────────────────────
# Instagram Stories
# ─────────────────────────────────────────────

def upload_ig_story(video_path):
    _check_config()
    if not META_IG_ID:
        return None

    file_size = os.path.getsize(video_path)

    # Step 1: 初始化 resumable upload container（限時動態）
    r = requests.post(f"{GRAPH}/{META_IG_ID}/media", params={
        "media_type": "STORIES",
        "upload_type": "resumable",
        "access_token": META_ACCESS_TOKEN,
    })
    r.raise_for_status()
    data = r.json()
    container_id = data.get("id")
    upload_url = data.get("uri")

    if not container_id or not upload_url:
        raise ValueError(f"IG Story 初始化失敗: {data}")

    # Step 2: 上傳影片 bytes
    with open(video_path, "rb") as f:
        upload_r = requests.post(upload_url, headers={
            "Authorization": f"OAuth {META_ACCESS_TOKEN}",
            "offset": "0",
            "file_size": str(file_size),
        }, data=f)
        upload_r.raise_for_status()

    # Step 3: 等待處理完成
    for _ in range(20):
        time.sleep(10)
        status_r = requests.get(f"{GRAPH}/{container_id}", params={
            "fields": "status_code",
            "access_token": META_ACCESS_TOKEN,
        })
        status = status_r.json().get("status_code")
        if status == "FINISHED":
            break
        if status == "ERROR":
            raise ValueError("IG Story 影片處理失敗")

    # Step 4: 發布
    pub_r = requests.post(f"{GRAPH}/{META_IG_ID}/media_publish", params={
        "creation_id": container_id,
        "access_token": META_ACCESS_TOKEN,
    })
    pub_r.raise_for_status()
    return pub_r.json().get("id")


def upload_reel(video_path, caption):
    """同時上傳到 FB Reels + IG Reels + IG 限時動態，回傳 (fb_id, ig_id)"""
    print(f"  📤 上傳到 Facebook Reels...")
    try:
        fb_id = upload_fb_reel(video_path, caption)
        print(f"  ✅ Facebook 完成：{fb_id}")
    except Exception as e:
        print(f"  ❌ Facebook 失敗：{e}")
        fb_id = None

    print(f"  📤 上傳到 Instagram Reels...")
    try:
        ig_id = upload_ig_reel(video_path, caption)
        print(f"  ✅ Instagram Reels 完成：{ig_id}")
    except Exception as e:
        print(f"  ❌ Instagram Reels 失敗：{e}")
        ig_id = None

    print(f"  📤 上傳到 Instagram 限時動態...")
    try:
        story_id = upload_ig_story(video_path)
        print(f"  ✅ Instagram 限時動態完成：{story_id}")
    except Exception as e:
        print(f"  ❌ Instagram 限時動態失敗：{e}")

    return fb_id, ig_id
