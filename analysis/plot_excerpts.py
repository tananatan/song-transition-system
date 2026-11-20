# I share the website excerpts so every plot uses exactly the same samples.
import argparse

import numpy as np


SONGS = [
    ("audio/Something_Elated.mp3", "Something Elated", "outgoing"),
    ("audio/Night_Owl.mp3", "Night Owl", "incoming"),
]


def website_requested():
    parser = argparse.ArgumentParser()
    parser.add_argument("--website", action="store_true", help="Export the 20-second website plot.")
    return parser.parse_args().website


def website_excerpt(audio, fs, role):
    sample_count = 20 * fs
    if len(audio) < sample_count:
        raise ValueError(f"The {role} song is shorter than 20 seconds.")

    # I slice by sample number so the outgoing clip ends at the actual end of the MP3.
    start_sample = len(audio) - sample_count if role == "outgoing" else 0
    end_sample = start_sample + sample_count
    clip = audio[start_sample:end_sample]
    return clip, start_sample / fs, end_sample / fs


def set_excerpt_axis(axis, start, end):
    # All time plots show five-second steps in the original song.
    ticks = np.linspace(start, end, 5)
    labels = [f"{tick:g}" if tick.is_integer() else f"{tick:.2f}" for tick in ticks]
    axis.set_xticks(ticks, labels=labels)
    axis.set_xlim(start, end)
    axis.set_xlabel("Time in original song (s)")
