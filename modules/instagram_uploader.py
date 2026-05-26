import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

import time
import requests
from pathlib import Path
import config

GRAPH_URL = "https://graph.instagram.com/v21.0"


def upload_reel(video_path: Path, script: dict) -> str:
    """Upload a video as an Instagram Reel. Returns the media ID."""
    token   = config.INSTAGRAM_ACCESS_TOKEN
    user_id = config.INSTAGRAM_ACCOUNT_ID

    title       = script.get("title", "")
    description = script.get("description", "")
    tags        = " ".join(f"#{t.replace(' ', '')}" for t in script.get("tags", []))
    caption     = f"{title}\n\n{description}\n\n{tags}"

    file_size = video_path.stat().st_size

    # Step 1: Create resumable upload container
    print("[instagram] Creating media container...")
    resp = requests.post(
        f"{GRAPH_URL}/{user_id}/media",
        data={
            "media_type":  "REELS",
            "upload_type": "resumable",
            "caption":     caption,
            "access_token": token,
        }
    )
    if not resp.ok:
        print(f"[instagram] Error response: {resp.text}")
    resp.raise_for_status()
    data = resp.json()
    container_id = data["id"]
    upload_url   = data["upload_url"]
    print(f"[instagram] Container ID: {container_id}")

    # Step 2: Upload video file
    print("[instagram] Uploading video...")
    with open(video_path, "rb") as f:
        video_data = f.read()

    upload_resp = requests.post(
        upload_url,
        headers={
            "Authorization": f"OAuth {token}",
            "offset":        "0",
            "file_size":     str(file_size),
        },
        data=video_data,
    )
    upload_resp.raise_for_status()
    print("[instagram] Upload complete.")

    # Step 3: Wait for processing
    print("[instagram] Waiting for processing...")
    for i in range(30):
        status_resp = requests.get(
            f"{GRAPH_URL}/{container_id}",
            params={"fields": "status_code", "access_token": token}
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
        }
    )
    pub_resp.raise_for_status()
    media_id = pub_resp.json()["id"]
    print(f"[instagram] Published! Media ID: {media_id}")
    return media_id
