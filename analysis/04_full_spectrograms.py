# Plot a spectrogram of each whole song to see when its frequencies show up.
import matplotlib.pyplot as plt
import numpy as np
from scipy.signal import stft

from plot_excerpts import ANALYSIS_FOLDER, SONGS, load_song

# Save the figures next to the other analysis plots.
plot_folder = ANALYSIS_FOLDER / "plots"
plot_folder.mkdir(exist_ok=True)

for filename, name, _ in SONGS:
    # Load all the samples. Divide their count by the sample rate to get seconds.
    audio, fs = load_song(filename, dtype="float32")
    duration = len(audio) / fs

    # The short-time Fourier transform (STFT) finds the frequencies in each short piece.
    # Each piece has 2048 samples, and neighboring pieces overlap by 1024 samples.
    frequencies, times, spectrum = stft(audio, fs=fs, nperseg=2048, noverlap=1024)
    # Magnitude tells us the strength of each frequency within each piece.
    # Decibels make quiet frequencies easier to see. The tiny floor avoids log(0).
    magnitude = np.abs(spectrum)
    decibels = 20 * np.log10(np.maximum(magnitude, 0.000001))

    # Time is on the x-axis, frequency is on the y-axis, and color shows signal strength.
    # Both songs use the same color limits so their colors can be compared.
    plt.figure(figsize=(10, 5))
    plt.imshow(decibels, origin="lower", aspect="auto",
               extent=[0, times[-1], 0, fs / 2], vmin=-100, vmax=-10)
    plt.xlim(0, duration)
    plt.xlabel("Time in the song (seconds)")
    plt.ylabel("Frequency (Hz)")
    plt.colorbar(label="STFT magnitude (dB relative to 1)")
    plt.title(f"{name}: full-song spectrogram")

    # Save each song in a separate file.
    plt.tight_layout()
    plot_path = plot_folder / f"{name.replace(' ', '_')}_full_spectrogram.png"
    plt.savefig(plot_path, dpi=150)
    plt.close()
    print(f"Saved {plot_path}")
    print(f"{name}: {duration:.2f} seconds, {fs} samples/second")
