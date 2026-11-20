# I plot the waveform and its RMS level for the section I picked from each song.
from pathlib import Path

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
    plt.suptitle("20-second waveform and RMS level")
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
    # I measure the signal level once per 50 ms block. Each point goes at the block's center.
    # RMS means square the samples, average them, and take the square root.
    size = int(0.05 * fs)
    levels = []
    times = []
    for beginning in range(0, len(clip) - size + 1, size):
        piece = clip[beginning:beginning + size]
        levels.append(np.sqrt(np.mean(piece ** 2)))
        times.append(start + (beginning + size / 2) / fs)
    levels = np.array(levels)
    times = np.array(times)
    # The blue line shows the individual samples. The orange line shows the RMS level.
    # RMS gives me a measure of signal strength over each block.
    time = start + np.arange(len(clip)) / fs
    plt.plot(time, clip, linewidth=0.5, label="Waveform")
    plt.plot(times, levels, color="orange", label="RMS level")
    plt.ylim((-1.05, 1.05) if website else (-1, 1))
    plt.legend()
    plt.title(name)
    plt.xlabel("Time in the original song (seconds)")
    plt.ylabel("Signal amplitude / RMS level")
    if website:
        set_excerpt_axis(plt.gca(), start, end)
    else:
        plt.xlim(start, end)

# I save the plot as a PNG that I can open in VS Code.
plt.tight_layout()
plot_path = plot_folder / ("01_waveform_rms.png" if website else "01_waveform_loudness.png")
plt.savefig(plot_path, dpi=150)
plt.close()
print(f"Saved {plot_path}")

