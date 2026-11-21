# Plot how bass energy changes during each 20-second excerpt.
import matplotlib.pyplot as plt
import numpy as np
from scipy.signal import spectrogram

from song_tools import ANALYSIS_FOLDER, SONGS, load_song, set_excerpt_axis, song_excerpt


# Use one shared y-axis so the two songs' bass levels can be compared.
plot_folder = ANALYSIS_FOLDER / "website_plots"
plot_folder.mkdir(exist_ok=True)

figure, axes = plt.subplots(2, 1, figsize=(10, 7), sharey=True, layout="constrained")
figure.suptitle("20-second bass energy (30–250 Hz)")

for axis, (filename, name, role) in zip(axes, SONGS):
    # Pull the same section used by the other website plots.
    audio, fs = load_song(filename)
    clip, start, end = song_excerpt(audio, fs, role, seconds=20)

    # Estimate power per Hz in Hann-windowed frames. A longer window resolves bass frequencies.
    frequencies, times, density = spectrogram(
        clip, fs=fs, window="hann", nperseg=8192, noverlap=6144,
        detrend=False, scaling="density", mode="psd",
    )

    # Sum power from 30 to 250 Hz and convert it to dB on a shared scale.
    in_band = (frequencies >= 30) & (frequencies <= 250)
    bin_width = frequencies[1] - frequencies[0]
    bass_power = np.sum(density[in_band], axis=0) * bin_width
    level = 10 * np.log10(np.maximum(bass_power, 1e-12))

    # Plot against time from the beginning of each original song.
    axis.plot(start + times, level, color="tab:blue")
    axis.set_title(f"{name} ({role})")
    axis.set_ylabel("Bass power (dB re 1 unit²)")
    axis.grid(axis="y", alpha=0.25)
    set_excerpt_axis(axis, start, end)

# Save both bass traces in one PNG.
plot_path = plot_folder / "06_bass_energy.png"
figure.savefig(plot_path, dpi=150)
plt.close(figure)
print(f"Saved {plot_path}")
