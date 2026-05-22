import wave
import struct
import math
import random
from pathlib import Path

import numpy as np


def generate_ambient_bgm(duration: float, output_path: Path, sample_rate: int = 44100) -> Path:
    n = int(sample_rate * duration)
    t = np.linspace(0, duration, n, dtype=np.float64)

    # Dm pentatonic atmosphere: D2, A2, D3, F3, A3, C4
    freqs = [73.42, 110.00, 146.83, 174.61, 220.00, 261.63]

    # Very slow LFOs for organic movement
    lfo1 = 0.5 + 0.5 * np.sin(2 * np.pi * 0.05 * t)   # 20s cycle
    lfo2 = 0.5 + 0.5 * np.sin(2 * np.pi * 0.08 * t + 1.2)
    lfo3 = 0.5 + 0.5 * np.sin(2 * np.pi * 0.03 * t + 0.7)

    signal = np.zeros(n, dtype=np.float64)

    # Layered drone tones with individual LFO modulation
    weights = [0.30, 0.18, 0.22, 0.12, 0.14, 0.08]
    lfo_map = [lfo1, lfo3, lfo2, lfo1, lfo3, lfo2]

    for freq, w, lfo in zip(freqs, weights, lfo_map):
        # Fundamental + subtle harmonic
        tone = np.sin(2 * np.pi * freq * t)
        tone += 0.25 * np.sin(2 * np.pi * freq * 2 * t + 0.3)
        tone += 0.10 * np.sin(2 * np.pi * freq * 3 * t + 0.6)
        signal += w * tone * lfo

    # Shimmer layer — high sparse overtones
    shimmer_freqs = [523.25, 659.25, 783.99]  # C5, E5, G5
    for sf in shimmer_freqs:
        shimmer_lfo = 0.5 + 0.5 * np.sin(2 * np.pi * random.uniform(0.04, 0.09) * t + random.uniform(0, 3))
        signal += 0.03 * np.sin(2 * np.pi * sf * t) * shimmer_lfo

    # Breath texture — filtered white noise
    noise = np.random.randn(n) * 0.015
    # Simple low-pass via cumulative sum trick (very gentle)
    window = 512
    kernel = np.ones(window) / window
    noise = np.convolve(noise, kernel, mode='same')
    signal += noise

    # Normalize
    peak = np.max(np.abs(signal))
    if peak > 0:
        signal = signal / peak * 0.72

    # Fade in 4s, fade out 4s
    fade = int(sample_rate * 4)
    signal[:fade] *= np.linspace(0, 1, fade)
    signal[-fade:] *= np.linspace(1, 0, fade)

    # Convert to stereo with subtle difference between channels
    delay_samples = int(sample_rate * 0.012)  # 12ms stereo spread
    left = signal
    right = np.roll(signal, delay_samples)
    stereo = np.stack([left, right], axis=1)

    # Write WAV
    output_path.parent.mkdir(parents=True, exist_ok=True)
    pcm = (stereo * 32767).astype(np.int16)
    with wave.open(str(output_path), "w") as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(pcm.tobytes())

    return output_path
