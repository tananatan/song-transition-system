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
    # Each sample has a time equal to its sample number divided by the sample rate.
    time = starts[i] + np.arange(len(clip)) / fs
    # The waveform shows the positive and negative values of the audio signal.
    plt.plot(time, clip, linewidth=0.5)
    plt.ylim(-1, 1)
    plt.title(names[i])
    plt.xlabel("Time in the original song (seconds)")
    plt.ylabel("Signal amplitude")
    plt.xlim(starts[i], ends[i])

# We leave room for the labels and save the plot before displaying it.
plt.tight_layout()
plt.savefig("simple_waveform.png", dpi=150)
plt.show()
