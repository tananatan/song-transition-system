# I use librosa to estimate where the beats fall in each selected section.
from pathlib import Path

import librosa
import numpy as np
import soundfile as sf
import matplotlib.pyplot as plt

from plot_excerpts import SONGS, set_excerpt_axis, website_excerpt, website_requested

# Website figures use their own output folder and 20-second excerpts.
website = website_requested()
folder = Path(__file__).resolve().parent
plot_folder = folder / ("website_plots" if website else "plots")
plot_folder.mkdir(exist_ok=True)

# The start and end times below are in seconds, in the same order as the songs.
starts = [208, 0]
ends = [232, 24]

plt.figure(figsize=(10, 7))
if website:
    plt.suptitle("20-second rhythm and candidate beats")
for i, (filename, name, role) in enumerate(SONGS):
    # I average the left and right channels for the analysis plots.
    audio, fs = sf.read(folder / filename)
    audio = np.mean(audio, axis=1)
    if website:
        clip, start, end = website_excerpt(audio, fs, role)
        name = f"{name} ({role})"
    else:
        # I keep the wider cue-search sections for a normal run.
        start, end = starts[i], ends[i]
        clip = audio[int(start * fs):int(end * fs)]
    # We put the first song on top and the second song underneath it.
    plt.subplot(2, 1, i + 1)
    # I measure RMS in 20 ms blocks so I can see short changes in signal level.
    # RMS means square the samples, average them, and take the square root.
    size = int(0.02 * fs)
    levels = []
    times = []
    for beginning in range(0, len(clip) - size + 1, size):
        piece = clip[beginning:beginning + size]
        levels.append(np.sqrt(np.mean(piece ** 2)))
        times.append(start + (beginning + size / 2) / fs)
    levels = np.array(levels)
    times = np.array(times)
    # I use librosa to measure where sounds start, including the quieter intro.
    onset_strength = librosa.onset.onset_strength(y=clip, sr=fs)
    cue_bpm = None
    if website:
        # I keep the BPM estimate from the wider cue-search section.
        cue_clip = audio[int(starts[i] * fs):int(ends[i] * fs)]
        cue_onsets = librosa.onset.onset_strength(y=cue_clip, sr=fs)
        cue_bpm = librosa.feature.tempo(onset_envelope=cue_onsets, sr=fs).item()

    # I track candidate beat times using the sound in the clip being plotted.
    tempo, clip_beat_times = librosa.beat.beat_track(
        onset_envelope=onset_strength, sr=fs, units="time", bpm=cue_bpm
    )
    tempo_bpm = np.asarray(tempo).item()
    # I add the clip start time so the markers line up with the original song.
    beat_times = start + clip_beat_times

    plt.plot(times, levels, label="RMS signal level")
    beat_label = "Candidate beats" if website else "Estimated beats (librosa)"
    plt.vlines(beat_times, 0, np.max(levels), colors="red", linestyles="dashed",
               alpha=0.5, label=beat_label)
    plt.ylim(bottom=0)
    plt.legend()
    if website:
        plt.title(f"{name} · {tempo_bpm:.1f} BPM (wider-clip estimate)")
    else:
        plt.title(f"{name} ({tempo_bpm:.1f} BPM estimate)")
    plt.xlabel("Time in the original song (seconds)")
    plt.ylabel("RMS signal level")
    if website:
        set_excerpt_axis(plt.gca(), start, end)
    else:
        plt.xlim(start, end)
    print(f"{name}: {tempo_bpm:.1f} BPM estimate, {len(beat_times)} candidate beats")

# I save the plot as a PNG that I can open in VS Code.
plt.tight_layout()
plot_path = plot_folder / ("03_candidate_beats.png" if website else "03_librosa_beats.png")
plt.savefig(plot_path, dpi=150)
plt.close()
print(f"Saved {plot_path}")

