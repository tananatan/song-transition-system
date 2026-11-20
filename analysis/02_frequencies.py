# Use a spectrogram to see which frequencies are active at each point in the excerpt.
import matplotlib.pyplot as plt
import numpy as np
from scipy.signal import stft

from plot_excerpts import (
    ANALYSIS_FOLDER, SONGS, load_song, set_excerpt_axis, song_excerpt, website_requested,
)

# Set up the output folder and pick the clip length.
website = website_requested()
excerpt_seconds = 20 if website else None
plot_folder = ANALYSIS_FOLDER / ("website_plots" if website else "plots")
plot_folder.mkdir(exist_ok=True)

# Put the two spectrograms on the same frequency scale.
figure, axes = plt.subplots(2, 1, figsize=(10, 7), sharey=True, layout="constrained")
if website:
    figure.suptitle("20-second STFT spectrograms")
for axis, (filename, name, role) in zip(axes, SONGS):
    # Load the song and cut out the section we are comparing.
    audio, fs = load_song(filename)
    clip, start, end = song_excerpt(audio, fs, role, excerpt_seconds)

    # The STFT measures frequency content in 2048-sample frames that overlap.
    frequencies, times, spectrum = stft(
        clip, fs=fs, window="hann", nperseg=2048, noverlap=1536,
        boundary=None, padded=False,
    )

    # Convert magnitude to dB so quieter frequencies show up. The floor avoids log(0).
    magnitude = np.abs(spectrum)
    decibels = 20 * np.log10(np.maximum(magnitude, 1e-6))

    # Add the clip start time and zoom in on the lowest 4000 Hz.
    mesh = axis.pcolormesh(
        start + times, frequencies, decibels, shading="auto", vmin=-80, vmax=-10,
    )
    axis.set_ylim(0, 4000)
    axis.set_title(f"{name} ({role})")
    axis.set_ylabel("Frequency (Hz)")
    if website:
        set_excerpt_axis(axis, start, end)
    else:
        axis.set_xlim(start, end)
        axis.set_xlabel("Time in the original song (seconds)")

# Save both panels with one colorbar because the dB scale is shared.
figure.colorbar(mesh, ax=axes, label="STFT magnitude (dB re 1)")
plot_path = plot_folder / ("02_stft_spectrogram.png" if website else "02_frequencies.png")
figure.savefig(plot_path, dpi=150)
plt.close(figure)
print(f"Saved {plot_path}")
