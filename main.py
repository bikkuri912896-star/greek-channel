import sys
import io
import argparse
import json
import shutil
from datetime import datetime
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

import config
from modules.script_generator import generate_script, TOPIC_POOL
from modules.tts_generator import generate_scene_audios
from modules.image_fetcher import fetch_images
from modules.video_creator import create_video
from modules.bgm_generator import generate_ambient_bgm
from modules.youtube_uploader import upload_video


def run_pipeline(topic: dict | None = None, upload: bool = True, dry_run: bool = False) -> dict:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    session_dir = config.SESSIONS_DIR / timestamp
    session_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n{'='*60}")
    print(f"[pipeline] Session: {timestamp}")

    # 1. Generate script
    print("[pipeline] Generating script via Claude...")
    script = generate_script(topic)
    topic_data = script.get("_topic", {})
    print(f"[pipeline] Topic: {topic_data.get('word', '')} ({topic_data.get('romanji', '')})")

    script_path = session_dir / "script.json"
    with open(script_path, "w", encoding="utf-8") as f:
        json.dump(script, f, ensure_ascii=False, indent=2)

    if dry_run:
        print("[pipeline] Dry run — stopping after script generation.")
        return {"script": script, "session_dir": str(session_dir)}

    # 2. Generate TTS audio
    # アウトロを強制固定（どんな場合も上書き）
    for scene in script.get("scenes", []):
        if scene.get("type") == "outro":
            scene["narration"] = "ぜひチャンネル登録をして、次の言葉もお聞きください。"
    print("[pipeline] Generating TTS audio...")
    scenes = script["scenes"]
    audio_paths = generate_scene_audios(scenes, session_dir)
    print(f"[pipeline] Generated {sum(1 for a in audio_paths if a)} audio files.")

    # 3. Fetch images
    print("[pipeline] Fetching images from Met Museum...")
    image_paths = fetch_images(topic_data, count=4)
    print(f"[pipeline] Fetched {len(image_paths)} images.")

    # 4. Generate BGM
    print("[pipeline] Generating ambient BGM...")
    bgm_path = session_dir / "bgm.wav"
    generate_ambient_bgm(duration=120.0, output_path=bgm_path)

    # 5. Create video
    print("[pipeline] Assembling video...")
    video_path = session_dir / f"video_{timestamp}.mp4"
    create_video(script, audio_paths, image_paths, video_path, bgm_path=bgm_path)
    print(f"[pipeline] Video saved: {video_path}")

    # Copy to output dir
    output_video = config.OUTPUT_DIR / f"{timestamp}.mp4"
    shutil.copy2(video_path, output_video)

    result = {
        "script": script,
        "video_path": str(output_video),
        "session_dir": str(session_dir),
    }

    # 5. Upload to YouTube
    if upload:
        print("[pipeline] Uploading to YouTube...")
        video_id = upload_video(output_video, script)
        result["youtube_id"] = video_id
        result["youtube_url"] = f"https://youtube.com/watch?v={video_id}"
        print(f"[pipeline] Done! {result['youtube_url']}")
    else:
        print(f"[pipeline] Done! Video at: {output_video}")

    return result


def main():
    parser = argparse.ArgumentParser(description="古典ギリシャ語チャンネル 動画生成パイプライン")
    parser.add_argument("--topic", type=str, help="ギリシャ語単語を指定（例: λόγος）")
    parser.add_argument("--no-upload", action="store_true", help="YouTubeアップロードをスキップ")
    parser.add_argument("--dry-run", action="store_true", help="スクリプト生成のみ実行")
    args = parser.parse_args()

    topic = None
    if args.topic:
        matches = [t for t in TOPIC_POOL if t["word"] == args.topic or t["romanji"] == args.topic]
        topic = matches[0] if matches else {"word": args.topic, "romanji": args.topic, "theme": args.topic}

    run_pipeline(
        topic=topic,
        upload=not args.no_upload,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    main()
