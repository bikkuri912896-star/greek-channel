import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

import time
import requests
from pathlib import Path
import config

GRAPH_URL = "https://graph.instagram.com/v21.0"


def _host_video(video_path: Path) -> str:
    """動画を一時的な公開ホスティングサービスにアップロードしてURLを返す。"""
    print("[instagram] Hosting video publicly...")

    # catbox.moe（無料・永続・アカウント不要）
    try:
        with open(video_path, "rb") as f:
            resp = requests.post(
                "https://catbox.moe/user/api.php",
                data={"reqtype": "fileupload"},
                files={"fileToUpload": (video_path.name, f, "video/mp4")},
                timeout=180,
            )
        resp.raise_for_status()
        url = resp.text.strip()
        if url.startswith("https://"):
            print(f"[instagram] Hosted at: {url}")
            return url
    except Exception as e:
        print(f"[instagram] catbox.moe failed: {e}")

    # litterbox.catbox.moe（72時間有効・フォールバック）
    with open(video_path, "rb") as f:
        resp = requests.post(
            "https://litterbox.catbox.moe/resources/internalpages/internals.php",
            data={"reqtype": "fileupload", "time": "72h"},
            files={"fileToUpload": (video_path.name, f, "video/mp4")},
            timeout=180,
        )
    resp.raise_for_status()
    url = resp.text.strip()
    print(f"[instagram] Hosted at (litterbox): {url}")
    return url


def upload_reel(video_path: Path, script: dict) -> str:
    """Upload a video as an Instagram Reel. Returns the media ID."""
    token   = config.INSTAGRAM_ACCESS_TOKEN
    user_id = config.INSTAGRAM_ACCOUNT_ID

    title       = script.get("title", "")
    description = script.get("description", "")
    tags        = " ".join(f"#{t.replace(' ', '')}" for t in script.get("tags", []))
    caption     = f"{title}\n\n{description}\n\n{tags}"

    # Step 1: Host video at a public URL
    video_url = _host_video(video_path)

    # Step 2: Create media container
    print("[instagram] Creating media container...")
    resp = requests.post(
        f"{GRAPH_URL}/{user_id}/media",
        data={
            "media_type":  "REELS",
            "video_url":   video_url,
            "caption":     caption,
            "access_token": token,
        },
        timeout=30,
    )
    if not resp.ok:
        print(f"[instagram] Error response: {resp.text}")
    resp.raise_for_status()
    container_id = resp.json()["id"]
    print(f"[instagram] Container ID: {container_id}")

    # Step 3: Wait for processing
    print("[instagram] Waiting for processing...")
    for i in range(30):
        status_resp = requests.get(
            f"{GRAPH_URL}/{container_id}",
            params={"fields": "status_code", "access_token": token},
        )
        status = status_resp.json().get("status_code", "")
        print(f"[instagram] Status: {status}")
        if status == "FINISHED":
            break
        if status == "ERROR":
            raise RuntimeError("Instagram media processing failed.")
        time.sleep(10)

    # Step 4: Publish
    print("[instagram] Publishing Reel...")
    pub_resp = requests.post(
        f"{GRAPH_URL}/{user_id}/media_publish",
        params={
            "creation_id":  container_id,
            "access_token": token,
        },
        timeout=30,
    )
    pub_resp.raise_for_status()
    media_id = pub_resp.json()["id"]
    print(f"[instagram] Published! Media ID: {media_id}")
    return media_id
