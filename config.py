import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).parent
load_dotenv(dotenv_path=BASE_DIR / ".env", override=True)
ASSETS_DIR = BASE_DIR / "assets"
BGM_DIR = ASSETS_DIR / "bgm"
CACHE_DIR = BASE_DIR / ".cache"
IMAGE_CACHE_DIR = CACHE_DIR / "images"
OUTPUT_DIR = BASE_DIR / "output"
SESSIONS_DIR = BASE_DIR / "sessions"
USED_TOPICS_FILE = BASE_DIR / "used_topics.json"

for d in [ASSETS_DIR, BGM_DIR, CACHE_DIR, IMAGE_CACHE_DIR, OUTPUT_DIR, SESSIONS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# Color palette
COLOR_BG = (8, 8, 16)
COLOR_GOLD = (201, 168, 76)
COLOR_CREAM = (240, 234, 214)
COLOR_DARK_GOLD = (140, 110, 40)
COLOR_SHADOW = (0, 0, 0)

# Fonts — bundled in fonts/ for cross-platform compatibility
import platform as _platform
_FONT_DIR = BASE_DIR / "fonts"
if _platform.system() == "Windows" and not _FONT_DIR.exists():
    # Fallback to system fonts on Windows if fonts/ not yet created
    FONT_PATH_MINCHO       = "C:/Windows/Fonts/yumindb.ttf"
    FONT_PATH_MINCHO_LIGHT = "C:/Windows/Fonts/yumin.ttf"
    FONT_PATH_GREEK        = "C:/Windows/Fonts/timesbd.ttf"
    FONT_PATH_GREEK_REGULAR= "C:/Windows/Fonts/times.ttf"
else:
    FONT_PATH_MINCHO       = str(_FONT_DIR / "yumindb.ttf")
    FONT_PATH_MINCHO_LIGHT = str(_FONT_DIR / "yumin.ttf")
    FONT_PATH_GREEK        = str(_FONT_DIR / "timesbd.ttf")
    FONT_PATH_GREEK_REGULAR= str(_FONT_DIR / "times.ttf")

# Video settings (Shorts: vertical 1080x1920)
VIDEO_WIDTH = 1080
VIDEO_HEIGHT = 1920
VIDEO_FPS = 24
VIDEO_CODEC = "libx264"
AUDIO_CODEC = "aac"
VIDEO_BITRATE = "4000k"

# TTS settings — downer female voice
TTS_VOICE = "ja-JP-KeitaNeural"
TTS_RATE = "-10%"
TTS_PITCH = "-20Hz"
TTS_VOLUME = "+0%"

# Channel identity
CHANNEL_NAME = "古典ギリシャの美"
CHANNEL_TAGLINE = "古代の叡智を現代に"

# Claude model
CLAUDE_MODEL = "claude-sonnet-4-6"

# Met Museum API
MET_API_BASE = "https://collectionapi.metmuseum.org/public/collection/v1"
MET_DEPARTMENT_GREEK_ROMAN = 13

# YouTube upload settings
YOUTUBE_CATEGORY_ID = "27"  # Education
YOUTUBE_LANGUAGE = "ja"
YOUTUBE_PRIVACY = "public"

# Scheduling
SCHEDULE_TIME = "09:00"

# Instagram settings
INSTAGRAM_ACCESS_TOKEN = os.getenv("INSTAGRAM_ACCESS_TOKEN", "")
INSTAGRAM_ACCOUNT_ID   = os.getenv("INSTAGRAM_ACCOUNT_ID", "26696919866646522")

# API keys
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
YOUTUBE_CLIENT_SECRETS_FILE = os.getenv("YOUTUBE_CLIENT_SECRETS_FILE", "client_secrets.json")
YOUTUBE_TOKEN_FILE = str(BASE_DIR / "youtube_token.json")
YOUTUBE_SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
