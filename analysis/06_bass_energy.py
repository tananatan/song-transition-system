# I plot how the bass energy changes during each 20-second excerpt.
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import soundfile as sf
from scipy.signal import spectrogram

from plot_excerpts import SONGS, set_excerpt_axis, website_excerpt


folder = Path(__file__).resolve().parent
plot_folder = folder / "website_plots"
plot_folder.mkdir(exist_ok=True)

figure, axes = plt.subplots(2, 1, figsize=(10, 7), sharey=True, layout="constrained")
figure.suptitle("20-second bass energy (30–250 Hz)")

for axis, (filename, name, role) in zip(axes, SONGS):
    audio, fs = sf.read(folder / filename)
    audio = np.mean(audio, axis=1)
    clip, start, end = website_excerpt(audio, fs, role)

    # I estimate power per Hz in short Hann-windowed frames.
    # 8192 samples per frame gives about 5.4 Hz between frequency bins.
    frequencies, times, density = spectrogram(
        clip, fs=fs, window="hann", nperseg=8192, noverlap=6144,
        detrend=False, scaling="density", mode="psd",
    )
    # I sum the power in the bass band and use a 1-unit mean-square reference.
    in_band = (frequencies >= 30) & (frequencies <= 250)
    bin_width = frequencies[1] - frequencies[0]
    bass_power = np.sum(density[in_band], axis=0) * bin_width
    level = 10 * np.log10(np.maximum(bass_power, 1e-12))

    axis.plot(start + times, level, color="tab:blue")
    axis.set_title(f"{name} ({role})")
    axis.set_ylabel("Bass power (dB re 1 unit²)")
    axis.grid(axis="y", alpha=0.25)
    set_excerpt_axis(axis, start, end)

plot_path = plot_folder / "06_bass_energy.png"
figure.savefig(plot_path, dpi=150)
plt.close(figure)
print(f"Saved {plot_path}")
