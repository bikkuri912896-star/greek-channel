import os
import time
import json
from pathlib import Path

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import config


def _get_credentials() -> Credentials:
    creds = None
    token_file = config.YOUTUBE_TOKEN_FILE

    if os.path.exists(token_file):
        creds = Credentials.from_authorized_user_file(token_file, config.YOUTUBE_SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                config.YOUTUBE_CLIENT_SECRETS_FILE,
                config.YOUTUBE_SCOPES,
            )
            creds = flow.run_local_server(port=0)
        with open(token_file, "w") as f:
            f.write(creds.to_json())

    return creds


def upload_video(video_path: Path, script: dict) -> str:
    creds = _get_credentials()
    youtube = build("youtube", "v3", credentials=creds)

    title = script.get("title", "古典ギリシャ語の美")
    description = script.get("description", "")
    tags = script.get("tags", []) + ["古典ギリシャ語", "哲学", "語源", "言語学", "教育"]

    body = {
        "snippet": {
            "title": title[:100],
            "description": description[:5000],
            "tags": tags[:500],
            "categoryId": config.YOUTUBE_CATEGORY_ID,
            "defaultLanguage": config.YOUTUBE_LANGUAGE,
            "defaultAudioLanguage": config.YOUTUBE_LANGUAGE,
        },
        "status": {
            "privacyStatus": config.YOUTUBE_PRIVACY,
            "selfDeclaredMadeForKids": False,
        },
    }

    media = MediaFileUpload(
        str(video_path),
        mimetype="video/mp4",
        resumable=True,
        chunksize=50 * 1024 * 1024,
    )

    request = youtube.videos().insert(
        part=",".join(body.keys()),
        body=body,
        media_body=media,
    )

    response = None
    retry = 0
    while response is None:
        try:
            status, response = request.next_chunk()
            if status:
                pct = int(status.progress() * 100)
                print(f"[uploader] Upload progress: {pct}%")
        except Exception as e:
            retry += 1
            if retry > 5:
                raise
            print(f"[uploader] Retry {retry}/5 after error: {e}")
            time.sleep(5 * retry)

    video_id = response.get("id", "")
    print(f"[uploader] Uploaded successfully: https://youtube.com/watch?v={video_id}")
    return video_id
