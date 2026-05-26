"""
Instagram バックフィルスクリプト
used_topics.json に記録済みの全単語の動画を再生成し、
Instagramにのみ投稿する（YouTubeには投稿しない）。
"""
import sys
import io
import json
import shutil
from datetime import datetime
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

import config
from modules.script_generator import TOPIC_POOL, generate_script
from modules.tts_generator import generate_scene_audios
from modules.image_fetcher import fetch_images
from modules.video_creator import create_video
from modules.bgm_generator import generate_ambient_bgm
from modules.instagram_uploader import upload_reel


def load_used_topics() -> list:
    if config.USED_TOPICS_FILE.exists():
        with open(config.USED_TOPICS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def main():
    used_words = load_used_topics()
    print(f"[backfill] 投稿済みトピック数: {len(used_words)}")

    # TOPIC_POOLから対象トピックを抽出（used_topicsの順番通りに処理）
    topic_map = {t["word"]: t for t in TOPIC_POOL}
    targets = [topic_map[w] for w in used_words if w in topic_map]
    print(f"[backfill] 処理対象: {len(targets)} 件")

    success = 0
    failed = []

    for i, topic in enumerate(targets):
        word = topic["word"]
        print(f"\n{'='*60}")
        print(f"[backfill] ({i+1}/{len(targets)}) {word} ({topic['romanji']})")

        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            session_dir = config.SESSIONS_DIR / f"backfill_{timestamp}"
            session_dir.mkdir(parents=True, exist_ok=True)

            # 1. スクリプト生成
            print("[backfill] Generating script...")
            script = generate_script(topic)

            script_path = session_dir / "script.json"
            with open(script_path, "w", encoding="utf-8") as f:
                json.dump(script, f, ensure_ascii=False, indent=2)

            # 2. TTS音声生成
            print("[backfill] Generating TTS...")
            scenes = script["scenes"]
            audio_paths = generate_scene_audios(scenes, session_dir)

            # 3. 画像取得
            print("[backfill] Fetching images...")
            image_paths = fetch_images(topic, count=4)

            # 4. BGM生成
            print("[backfill] Generating BGM...")
            bgm_path = session_dir / "bgm.wav"
            generate_ambient_bgm(duration=120.0, output_path=bgm_path)

            # 5. 動画生成
            print("[backfill] Creating video...")
            video_path = session_dir / f"video_{timestamp}.mp4"
            create_video(script, audio_paths, image_paths, video_path, bgm_path=bgm_path)

            output_video = config.OUTPUT_DIR / f"backfill_{timestamp}.mp4"
            shutil.copy2(video_path, output_video)

            # 6. Instagramにのみ投稿
            print("[backfill] Uploading to Instagram...")
            media_id = upload_reel(output_video, script)
            print(f"[backfill] Instagram OK: {media_id}")
            success += 1

        except Exception as e:
            print(f"[backfill] ERROR for {word}: {e}")
            failed.append(word)

    print(f"\n{'='*60}")
    print(f"[backfill] 完了: 成功 {success} / {len(targets)}")
    if failed:
        print(f"[backfill] 失敗: {failed}")


if __name__ == "__main__":
    main()
