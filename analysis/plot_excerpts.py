# Share the audio files, clip selection, and RMS calculation across scripts.
import argparse
from pathlib import Path

import librosa
import numpy as np
import soundfile as sf


# Keep all paths relative to this folder, including when running from VS Code.
ANALYSIS_FOLDER = Path(__file__).resolve().parent
SONGS = [
    ("audio/Something_Elated.mp3", "Something Elated", "outgoing"),
    ("audio/Night_Owl.mp3", "Night Owl", "incoming"),
]
TEMPO_GUESSES = {"outgoing": 88, "incoming": 129}
BEAT_HOP = 512


def load_song(filename, dtype="float64"):
    # Average the channels into a mono copy for analysis.
    path = ANALYSIS_FOLDER / filename
    if not path.is_file():
        raise SystemExit(f"Put {path.name} in {path.parent} and run the script again.")
    audio, fs = sf.read(path, dtype=dtype, always_2d=True)
    return audio.mean(axis=1), fs


def website_requested():
    # The --website option selects the shorter plots for the project website.
    parser = argparse.ArgumentParser()
    parser.add_argument("--website", action="store_true", help="Export the 20-second website plot.")
    return parser.parse_args().website


def song_excerpt(audio, fs, role, seconds=None):
    # Use the last 20% of the outgoing song and the first 20% of the incoming song by default.
    # The website scripts pass 20 seconds so those plots show exactly the same clips.
    sample_count = len(audio) // 5 if seconds is None else round(seconds * fs)
    if not 0 < sample_count <= len(audio):
        raise ValueError(f"The {role} song is too short for the requested excerpt.")

    # Slice by sample number and return the times in the original song.
    start_sample = len(audio) - sample_count if role == "outgoing" else 0
    end_sample = start_sample + sample_count
    clip = audio[start_sample:end_sample]
    return clip, start_sample / fs, end_sample / fs


def short_time_rms(audio, fs, seconds=0.05):
    # Keep only full blocks. RMS is the square root of the mean squared samples.
    block_size = max(1, int(seconds * fs))
    block_count = len(audio) // block_size
    blocks = audio[:block_count * block_size].reshape(block_count, block_size)
    levels = np.sqrt(np.mean(blocks ** 2, axis=1))

    # Give each RMS measurement the time at the center of its block.
    times = (np.arange(block_count) + 0.5) * block_size / fs
    return times, levels


def find_beats(clip, fs, role, tempo_clip=None):
    # Use increases in the sound to find attacks. A website plot can use a
    # longer clip for estimating tempo while placing beats in its shorter clip.
    onsets = librosa.onset.onset_strength(y=clip, sr=fs, hop_length=BEAT_HOP)
    tempo_onsets = onsets
    if tempo_clip is not None:
        tempo_onsets = librosa.onset.onset_strength(y=tempo_clip, sr=fs, hop_length=BEAT_HOP)

    # Start the tempo estimate near the BPM noted in the plan, then track beats in the audio.
    bpm = librosa.feature.tempo(
        onset_envelope=tempo_onsets, sr=fs, hop_length=BEAT_HOP, start_bpm=TEMPO_GUESSES[role],
    ).item()
    _, frames = librosa.beat.beat_track(
        onset_envelope=onsets, sr=fs, hop_length=BEAT_HOP, bpm=bpm,
    )
    return bpm, frames, onsets


def set_excerpt_axis(axis, start, end):
    # All time plots show five-second steps in the original song.
    ticks = np.linspace(start, end, 5)
    labels = [f"{tick:g}" if tick.is_integer() else f"{tick:.2f}" for tick in ticks]
    axis.set_xticks(ticks, labels=labels)
    axis.set_xlim(start, end)
    axis.set_xlabel("Time in original song (s)")
