import sys, io
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

import time
import os
import requests
from pathlib import Path
import config

TIKTOK_API = "https://open.tiktokapis.com/v2"


def _refresh_access_token() -> str:
    """リフレッシュトークンで新しいアクセストークンを取得する。"""
    refresh_token = os.environ.get("TIKTOK_REFRESH_TOKEN", "")
    client_key    = os.environ.get("TIKTOK_CLIENT_KEY", "")
    client_secret = os.environ.get("TIKTOK_CLIENT_SECRET", "")

    resp = requests.post(
        f"{TIKTOK_API}/oauth/token/",
        data={
            "client_key":     client_key,
            "client_secret":  client_secret,
            "grant_type":     "refresh_token",
            "refresh_token":  refresh_token,
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=30,
    )
    data = resp.json()
    if "access_token" not in data:
        raise RuntimeError(f"Token refresh failed: {data}")
    print(f"[tiktok] Token refreshed.")
    return data["access_token"]


def upload_video(video_path: Path, script: dict) -> str:
    """TikTokに動画を投稿する。Returns post_id."""

    # アクセストークンを取得（まずリフレッシュ）
    print("[tiktok] Refreshing access token...")
    try:
        access_token = _refresh_access_token()
    except Exception as e:
        print(f"[tiktok] Refresh failed, using stored token: {e}")
        access_token = os.environ.get("TIKTOK_ACCESS_TOKEN", "")

    title = script.get("title", "")[:150]  # TikTokのタイトル上限150文字
    tags  = " ".join(f"#{t.replace(' ', '')}" for t in script.get("tags", []))
    caption = f"{title}\n{tags}"[:2200]

    file_size = video_path.stat().st_size

    # Step 1: 動画アップロードの初期化
    print("[tiktok] Initializing video upload...")
    init_resp = requests.post(
        f"{TIKTOK_API}/post/publish/video/init/",
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type":  "application/json; charset=UTF-8",
        },
        json={
            "post_info": {
                "title":        caption,
                "privacy_level": "SELF_ONLY",  # テスト中はSELF_ONLYで投稿
                "disable_duet":    False,
                "disable_comment": False,
                "disable_stitch":  False,
            },
            "source_info": {
                "source":         "FILE_UPLOAD",
                "video_size":     file_size,
                "chunk_size":     file_size,
                "total_chunk_count": 1,
            },
        },
        timeout=30,
    )
    if not init_resp.ok:
        print(f"[tiktok] Init error: {init_resp.text}")
    init_resp.raise_for_status()
    init_data   = init_resp.json().get("data", {})
    publish_id  = init_data.get("publish_id")
    upload_url  = init_data.get("upload_url")
    print(f"[tiktok] Publish ID: {publish_id}")

    # Step 2: 動画ファイルをアップロード
    print("[tiktok] Uploading video file...")
    with open(video_path, "rb") as f:
        video_data = f.read()

    upload_resp = requests.put(
        upload_url,
        headers={
            "Content-Type":          "video/mp4",
            "Content-Range":         f"bytes 0-{file_size - 1}/{file_size}",
            "Content-Length":        str(file_size),
        },
        data=video_data,
        timeout=300,
    )
    if not upload_resp.ok:
        print(f"[tiktok] Upload error: {upload_resp.text}")
    upload_resp.raise_for_status()
    print("[tiktok] Video uploaded.")

    # Step 3: 投稿状態を確認
    print("[tiktok] Checking post status...")
    for i in range(30):
        status_resp = requests.post(
            f"{TIKTOK_API}/post/publish/status/fetch/",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type":  "application/json; charset=UTF-8",
            },
            json={"publish_id": publish_id},
            timeout=30,
        )
        status_data = status_resp.json().get("data", {})
        status = status_data.get("status", "")
        print(f"[tiktok] Status: {status}")
        if status == "PUBLISH_COMPLETE":
            break
        if status in ("FAILED", "SPAM_REVIEW_FAILED"):
            raise RuntimeError(f"TikTok post failed: {status_data}")
        time.sleep(10)

    print(f"[tiktok] Posted! Publish ID: {publish_id}")
    return publish_id
