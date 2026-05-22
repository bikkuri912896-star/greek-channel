import subprocess
import textwrap
import unicodedata
import random
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import (
    VideoClip,
    concatenate_videoclips,
    AudioFileClip,
)
import imageio_ffmpeg
import config

W, H = config.VIDEO_WIDTH, config.VIDEO_HEIGHT   # 1080 x 1920


# ── ffmpeg helper ─────────────────────────────────────────────────────────────

def _ff():
    return imageio_ffmpeg.get_ffmpeg_exe()


# ── Font helpers ──────────────────────────────────────────────────────────────

def _font_jp(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    path = config.FONT_PATH_MINCHO if bold else config.FONT_PATH_MINCHO_LIGHT
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        return ImageFont.load_default()


def _font_gr(size: int, bold: bool = True) -> ImageFont.FreeTypeFont:
    """Times New Roman for polytonic Greek — always pure Latin/Greek, no CJK."""
    path = config.FONT_PATH_GREEK if bold else config.FONT_PATH_GREEK_REGULAR
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        return _font_jp(size, bold)


def _nfc(text: str) -> str:
    return unicodedata.normalize("NFC", text)


# ── Drawing helpers ───────────────────────────────────────────────────────────

def _text_w(draw: ImageDraw.ImageDraw, text: str, font) -> int:
    bb = draw.textbbox((0, 0), text, font=font)
    return bb[2] - bb[0]


def _draw_centered(draw, text: str, cy: int, font, color: tuple,
                   shadow: bool = True, wrap: int = 18):
    lines = []
    for para in _nfc(text).split("\n"):
        lines.extend(textwrap.wrap(para, width=wrap) if para.strip() else [""])
    lh = font.size + 10
    y = cy - (lh * len(lines)) // 2
    for line in lines:
        tw = _text_w(draw, line, font)
        x = (W - tw) // 2
        if shadow:
            draw.text((x + 3, y + 3), line, font=font, fill=(0, 0, 0))
        draw.text((x, y), line, font=font, fill=color)
        y += lh


def _gold_line(draw, y: int, width: int = 700):
    x0 = (W - width) // 2
    draw.rectangle([x0, y, x0 + width, y + 2], fill=config.COLOR_GOLD)


def _subtitle_bar(draw, text: str, font):
    """Pure-Japanese narration subtitle — always rendered with JP font."""
    lines = textwrap.wrap(_nfc(text), width=20)
    lh = font.size + 8
    total = lh * len(lines)
    bar_top = H - total - 80
    draw.rectangle([0, bar_top - 16, W, H - 40], fill=(0, 0, 0, 180))
    y = bar_top
    for line in lines:
        tw = _text_w(draw, line, font)
        draw.text(((W - tw) // 2, y), line, font=font, fill=config.COLOR_CREAM)
        y += lh


# ── Background image helper ───────────────────────────────────────────────────

def _load_bg(image_path: Path) -> np.ndarray:
    img = Image.open(image_path).convert("RGB")
    ir = img.width / img.height
    tr = W / H
    nw, nh = (int(H * ir), H) if ir > tr else (W, int(W / ir))
    img = img.resize((nw, nh), Image.LANCZOS)
    img = img.crop(((nw - W) // 2, (nh - H) // 2,
                    (nw - W) // 2 + W, (nh - H) // 2 + H))
    overlay = Image.new("RGB", (W, H), config.COLOR_BG)
    return np.array(Image.blend(img, overlay, 0.60))


# ── Audio duration helpers ────────────────────────────────────────────────────

def _audio_file_dur(path) -> float:
    if path and Path(path).exists():
        try:
            a = AudioFileClip(str(path))
            d = a.duration
            a.close()
            return d
        except Exception:
            pass
    return 0.0


def _scene_dur(audio_path, padding=0.5, minimum=4.0) -> float:
    d = _audio_file_dur(audio_path)
    return max(d + padding, minimum) if d > 0 else minimum


# ── Scene clip builders (video only, no audio) ────────────────────────────────

def _intro_clip(scene: dict, dur: float) -> VideoClip:
    f_ch = _font_jp(62, bold=True)
    f_tg = _font_jp(32)
    f_nt = _font_jp(36, bold=True)

    def frame(t):
        img = Image.new("RGB", (W, H), config.COLOR_BG)
        draw = ImageDraw.Draw(img)
        fade = min(t / 1.2, 1.0)
        gold = tuple(int(c * fade) for c in config.COLOR_GOLD)
        cream = tuple(int(c * fade) for c in config.COLOR_CREAM)
        _gold_line(draw, 160)
        _draw_centered(draw, config.CHANNEL_NAME, 260, f_ch, gold)
        _gold_line(draw, 318)
        _draw_centered(draw, config.CHANNEL_TAGLINE, 390, f_tg, cream, shadow=False)
        narration = scene.get("narration", "")
        if narration:
            _subtitle_bar(draw, narration, f_nt)
        return np.array(img)

    return VideoClip(frame, duration=dur)


def _word_clip(scene: dict, dur: float) -> VideoClip:
    f_gr = _font_gr(160, bold=True)
    f_rm = _font_gr(52, bold=False)
    f_rd = _font_jp(40)
    f_nt = _font_jp(34, bold=True)

    def frame(t):
        img = Image.new("RGB", (W, H), config.COLOR_BG)
        draw = ImageDraw.Draw(img)
        fade = min(t / 0.8, 1.0)
        # Soft glow rings
        for r in range(6, 0, -1):
            v = int(20 * r * fade // 6)
            pad = r * 55
            draw.ellipse([(W//2 - 240 - pad, H//2 - 240 - pad),
                          (W//2 + 240 + pad, H//2 + 240 + pad)],
                         fill=(v, int(v * 0.8), 0))
        gold = tuple(int(c * fade) for c in config.COLOR_GOLD)
        cream = tuple(int(c * fade) for c in config.COLOR_CREAM)
        _gold_line(draw, H // 2 - 270)
        _draw_centered(draw, _nfc(scene.get("greek_text", "")),
                       H // 2 - 60, f_gr, gold)
        _draw_centered(draw, _nfc(scene.get("romanji", "")),
                       H // 2 + 100, f_rm, cream, shadow=False)
        reading = scene.get("reading", "")
        if reading:
            _draw_centered(draw, reading, H // 2 + 185, f_rd,
                           config.COLOR_CREAM, shadow=False)
        _gold_line(draw, H // 2 + 235)
        narration = scene.get("narration", "")
        if narration:
            _subtitle_bar(draw, narration, f_nt)
        return np.array(img)

    return VideoClip(frame, duration=dur)


def _meaning_clip(scene: dict, image_path, dur: float) -> VideoClip:
    f_sub = _font_jp(44, bold=True)
    f_qt  = _font_gr(48, bold=True)   # Greek font for quote text only
    f_src = _font_jp(30)
    f_nt  = _font_jp(34, bold=True)
    bg_arr = _load_bg(image_path) if image_path else None

    def frame(t):
        if bg_arr is not None:
            zoom = 1.0 + 0.05 * (t / dur)
            nw, nh = int(W * zoom), int(H * zoom)
            bg_img = Image.fromarray(bg_arr).resize((nw, nh), Image.BILINEAR)
            img = bg_img.crop(((nw-W)//2, (nh-H)//2, (nw-W)//2+W, (nh-H)//2+H))
        else:
            img = Image.new("RGB", (W, H), config.COLOR_BG)
        draw = ImageDraw.Draw(img)
        fade = min(t / 1.5, 1.0)
        gold = tuple(int(c * fade) for c in config.COLOR_GOLD)
        cream = tuple(int(c * fade) for c in config.COLOR_CREAM)
        subtitle = scene.get("subtitle", "")
        if subtitle:
            _gold_line(draw, 120)
            _draw_centered(draw, subtitle, 210, f_sub, gold, wrap=14)
            _gold_line(draw, 268)
        greek_quote = scene.get("greek_quote", "")
        if greek_quote:
            # Use only Western characters around the Greek quote
            _draw_centered(draw, _nfc(f"-- {greek_quote} --"),
                           H // 2 - 50, f_qt, gold, wrap=20)
            src = scene.get("quote_source", "")
            if src:
                _draw_centered(draw, src, H // 2 + 70, f_src, cream, shadow=False)
        narration = scene.get("narration", "")
        if narration:
            _subtitle_bar(draw, narration, f_nt)
        return np.array(img)

    return VideoClip(frame, duration=dur)


def _outro_clip(scene: dict, dur: float) -> VideoClip:
    f_ch = _font_jp(58, bold=True)
    f_tg = _font_jp(34)
    f_ct = _font_jp(38, bold=True)
    f_nt = _font_jp(34, bold=True)

    def frame(t):
        img = Image.new("RGB", (W, H), config.COLOR_BG)
        draw = ImageDraw.Draw(img)
        fade = min(t / 1.2, 1.0)
        fade_out = 1.0 - max((t - (dur - 1.5)) / 1.5, 0.0)
        a = min(fade, fade_out)
        gold = tuple(int(c * a) for c in config.COLOR_GOLD)
        cream = tuple(int(c * a) for c in config.COLOR_CREAM)
        _gold_line(draw, H // 2 - 180)
        _draw_centered(draw, config.CHANNEL_NAME, H // 2 - 70, f_ch, gold)
        _draw_centered(draw, config.CHANNEL_TAGLINE, H // 2 + 30, f_tg,
                       cream, shadow=False)
        _gold_line(draw, H // 2 + 82)
        _draw_centered(draw, "チャンネル登録 & 高評価", H // 2 + 170, f_ct, cream)
        narration = scene.get("narration", "")
        if narration:
            _subtitle_bar(draw, narration, f_nt)
        return np.array(img)

    return VideoClip(frame, duration=dur)


# ── ffmpeg audio pipeline (bypasses MoviePy audio entirely) ──────────────────

def _build_audio(audio_paths: list, scene_durs: list, bgm_path,
                 total_dur: float, out_path: Path):
    ff = _ff()
    valid = [(str(p), d) for p, d in zip(audio_paths, scene_durs)
             if p and Path(p).exists()]

    narr_path = out_path.parent / "_narr.aac"

    if valid:
        # Concatenate narrations, padding each to its scene duration
        inputs = []
        fparts = []
        for i, (p, dur) in enumerate(valid):
            inputs += ["-i", p]
            fparts.append(f"[{i}:a]apad=whole_dur={dur:.3f}[a{i}]")
        concat_in = "".join(f"[a{i}]" for i in range(len(valid)))
        fc = ";".join(fparts) + f";{concat_in}concat=n={len(valid)}:v=0:a=1[out]"
        subprocess.run(
            [ff] + inputs + [
                "-filter_complex", fc,
                "-map", "[out]",
                "-c:a", "aac", "-b:a", "192k",
                "-t", f"{total_dur:.3f}",
                "-y", str(narr_path),
            ],
            capture_output=True, check=True,
        )
    else:
        # Pure silence
        subprocess.run(
            [ff, "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
             "-t", f"{total_dur:.3f}", "-c:a", "aac", "-b:a", "128k",
             "-y", str(narr_path)],
            capture_output=True, check=True,
        )

    if bgm_path and Path(bgm_path).exists():
        subprocess.run(
            [ff,
             "-i", str(narr_path),
             "-stream_loop", "-1", "-i", str(bgm_path),
             "-filter_complex",
             "[0:a]volume=1.0[a1];[1:a]volume=0.08[a2];"
             "[a1][a2]amix=inputs=2:duration=first[out]",
             "-map", "[out]",
             "-c:a", "aac", "-b:a", "192k",
             "-t", f"{total_dur:.3f}",
             "-y", str(out_path)],
            capture_output=True, check=True,
        )
    else:
        out_path.write_bytes(narr_path.read_bytes())


def _mux(video_silent: Path, audio: Path, output: Path):
    subprocess.run(
        [_ff(),
         "-i", str(video_silent),
         "-i", str(audio),
         "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
         "-shortest", "-y", str(output)],
        check=True,
    )


# ── Main entry ────────────────────────────────────────────────────────────────

def create_video(script: dict, audio_paths: list, image_paths: list,
                 output_path: Path, bgm_path=None) -> Path:
    scenes = script["scenes"]
    img_pool = list(image_paths)
    random.shuffle(img_pool)
    img_idx = 0

    # Pre-compute durations
    scene_durs = [_scene_dur(audio_paths[i] if i < len(audio_paths) else None)
                  for i in range(len(scenes))]

    # Build video-only clips
    clips = []
    for i, scene in enumerate(scenes):
        dur = scene_durs[i]
        stype = scene.get("type", "")
        if stype == "intro":
            clip = _intro_clip(scene, dur)
        elif stype == "word":
            clip = _word_clip(scene, dur)
        elif stype == "meaning":
            img = img_pool[img_idx] if img_idx < len(img_pool) else None
            img_idx += 1
            clip = _meaning_clip(scene, img, dur)
        elif stype == "outro":
            clip = _outro_clip(scene, max(dur, 6.0))
            scene_durs[i] = max(dur, 6.0)
        else:
            clip = _meaning_clip(scene, None, dur)
        clips.append(clip)

    final = concatenate_videoclips(clips, method="chain")
    total_dur = final.duration

    output_path.parent.mkdir(parents=True, exist_ok=True)
    silent_path = output_path.parent / "_silent.mp4"
    audio_path  = output_path.parent / "_audio.aac"

    print(f"[video] Rendering {total_dur:.1f}s silent video...")
    final.write_videofile(
        str(silent_path),
        fps=config.VIDEO_FPS,
        codec=config.VIDEO_CODEC,
        audio=False,
        bitrate=config.VIDEO_BITRATE,
        threads=4,
        logger=None,
    )
    final.close()

    print("[video] Building audio track with ffmpeg...")
    _build_audio(
        audio_paths=audio_paths,
        scene_durs=scene_durs,
        bgm_path=bgm_path,
        total_dur=total_dur,
        out_path=audio_path,
    )

    print("[video] Muxing video + audio...")
    _mux(silent_path, audio_path, output_path)

    # Cleanup temp files
    for tmp in [silent_path, audio_path,
                output_path.parent / "_narr.aac"]:
        if tmp.exists():
            tmp.unlink()

    return output_path
