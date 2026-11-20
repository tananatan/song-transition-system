# I use a spectrogram to see how the frequencies change during each selected section.
from pathlib import Path

import numpy as np
import soundfile as sf
import matplotlib.pyplot as plt
from scipy.signal import stft

from plot_excerpts import SONGS, set_excerpt_axis, website_excerpt, website_requested

# Website figures use their own output folder and 20-second excerpts.
website = website_requested()
folder = Path(__file__).resolve().parent
plot_folder = folder / ("website_plots" if website else "plots")
plot_folder.mkdir(exist_ok=True)

# The start and end times below are in seconds, in the same order as the songs.
starts = [208, 0]
ends = [232, 24]

if website:
    figure, axes = plt.subplots(2, 1, figsize=(10, 7), sharey=True, layout="constrained")
    figure.suptitle("20-second STFT spectrograms")
else:
    plt.figure(figsize=(10, 7))
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
    # I stack the outgoing song above the incoming song.
    if website:
        plt.sca(axes[i])
    else:
        plt.subplot(2, 1, i + 1)
    # The short-time Fourier transform (STFT) finds the frequencies in each short piece.
    # Here each piece has 2048 samples and shares 1536 samples with the next piece.
    frequencies, times, spectrum = stft(clip, fs=fs, nperseg=2048, noverlap=1536,
                                        boundary=None, padded=False)
    # I turn the STFT values into decibels so weaker frequencies show up in the colors.
    # The small lower limit prevents us from taking the logarithm of zero.
    magnitude = np.abs(spectrum)
    decibels = 20 * np.log10(np.maximum(magnitude, 0.000001))
    # STFT times are relative to this clip, so I add its start time once.
    mesh = plt.pcolormesh(start + times, frequencies, decibels, shading="auto",
                         vmin=-80, vmax=-10)
    # I zoom in on 0 to 4000 Hz. Brighter colors show stronger frequencies.
    plt.ylim(0, 4000)
    if not website:
        plt.colorbar(label="Magnitude")
    plt.title(name)
    plt.xlabel("Time in the original song (seconds)")
    plt.ylabel("Frequency (Hz)")
    if website:
        set_excerpt_axis(plt.gca(), start, end)
    else:
        plt.xlim(start, end)

# I save the plot as a PNG that I can open in VS Code.
if website:
    # One colorbar works for both panels because their dB scales are identical.
    figure.colorbar(mesh, ax=axes, label="STFT magnitude (dB re 1)")
else:
    plt.tight_layout()
plot_path = plot_folder / ("02_stft_spectrogram.png" if website else "02_frequencies.png")
plt.savefig(plot_path, dpi=150)
plt.close()
print(f"Saved {plot_path}")

