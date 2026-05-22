import asyncio
from pathlib import Path
import edge_tts
import config


async def _synthesize(text: str, output_path: str):
    communicate = edge_tts.Communicate(
        text=text,
        voice=config.TTS_VOICE,
        rate=config.TTS_RATE,
        pitch=config.TTS_PITCH,
        volume=config.TTS_VOLUME,
    )
    await communicate.save(output_path)


def generate_audio(text: str, output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    asyncio.run(_synthesize(text, str(output_path)))
    return output_path


def generate_scene_audios(scenes: list, session_dir: Path) -> list:
    audio_paths = []
    for i, scene in enumerate(scenes):
        narration = scene.get("narration", "")
        if not narration:
            audio_paths.append(None)
            continue
        out = session_dir / f"audio_{i:02d}_{scene['type']}.mp3"
        generate_audio(narration, out)
        audio_paths.append(out)
    return audio_paths
