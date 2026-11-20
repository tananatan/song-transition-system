# Run this file with the SongTransition_Python_2026-11-15 folder as your working folder.
import numpy as np
import soundfile as sf
import matplotlib.pyplot as plt

# These are the two original songs and the sections we chose to study.
files = ["audio/Something_Elated.mp3", "audio/Night_Owl.mp3"]
names = ["Something Elated", "Night Owl"]
starts = [208, 0]
ends = [232, 24]

plt.figure(figsize=(10, 7))
for i in range(2):
    # Reading the file gives us audio samples and the sample rate in samples per second.
    audio, fs = sf.read(files[i])
    # We average the left and right channels to get one signal for analysis.
    audio = np.mean(audio, axis=1)
    # Multiplying seconds by the sample rate tells us which samples to keep.
    clip = audio[int(starts[i] * fs):int(ends[i] * fs)]
    # We put the first song on top and the second song underneath it.
    plt.subplot(2, 1, i + 1)
    # We split the audio into short pieces and measure the RMS of each piece.
    # RMS means square the samples, average them, and take the square root.
    size = int(0.05 * fs)
    levels = []
    times = []
    for beginning in range(0, len(clip) - size + 1, size):
        piece = clip[beginning:beginning + size]
        levels.append(np.sqrt(np.mean(piece ** 2)))
        times.append(starts[i] + (beginning + size / 2) / fs)
    levels = np.array(levels)
    times = np.array(times)
    # RMS shows signal strength, not an exact measurement of perceived loudness.
    plt.plot(times, levels)
    plt.ylim(bottom=0)
    plt.title(names[i])
    plt.xlabel("Time in the original song (seconds)")
    plt.ylabel("RMS signal level")
    plt.xlim(starts[i], ends[i])

# We leave room for the labels and save the plot before displaying it.
plt.tight_layout()
plt.savefig("simple_loudness.png", dpi=150)
plt.show()
