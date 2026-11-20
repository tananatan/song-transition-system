# Run this file with the SongTransition_Python_2026-11-15 folder as your working folder.
import numpy as np
import soundfile as sf
import matplotlib.pyplot as plt
from scipy.signal import stft
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
    # The STFT takes a Fourier transform of short overlapping pieces of the audio.
    # Here each piece has 2048 samples and shares 1536 samples with the next piece.
    frequencies, times, spectrum = stft(clip, fs=fs, nperseg=2048, noverlap=1536,
                                        boundary=None, padded=False)
    # Absolute value gives magnitude. Decibels help us see weaker frequencies too.
    # The small lower limit prevents us from taking the logarithm of zero.
    magnitude = np.abs(spectrum)
    decibels = 20 * np.log10(np.maximum(magnitude, 0.000001))
    plt.pcolormesh(starts[i] + times, frequencies, decibels, shading="auto",
                   vmin=-80, vmax=-10)
    # We display only 0 to 4000 Hz. The audio still contains higher frequencies.
    plt.ylim(0, 4000)
    plt.colorbar(label="Magnitude (dB relative to 1)")
    plt.title(names[i])
    plt.xlabel("Time in the original song (seconds)")
    plt.ylabel("Frequency (Hz)")
    plt.xlim(starts[i], ends[i])

# We leave room for the labels and save the plot before displaying it.
plt.tight_layout()
plt.savefig("simple_frequencies.png", dpi=150)
plt.show()
