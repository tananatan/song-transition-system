# I make a spectrogram of each whole song to see when different frequencies show up.
from pathlib import Path

import numpy as np
import soundfile as sf
import matplotlib.pyplot as plt
from scipy.signal import stft

# I look for the audio beside this script and save the figures in plots.
folder = Path(__file__).resolve().parent
plot_folder = folder / "plots"
plot_folder.mkdir(exist_ok=True)

files = ["audio/Something_Elated.mp3", "audio/Night_Owl.mp3"]
names = ["Something Elated", "Night Owl"]
outputs = ["Something_Elated_full_spectrogram.png", "Night_Owl_full_spectrogram.png"]

for i in range(2):
    # I load all the samples. fs tells me how many samples there are per second.
    audio, fs = sf.read(folder / files[i], dtype="float32")
    audio = np.mean(audio, axis=1)
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
    plt.title(names[i] + ": full-song spectrogram")
    plt.tight_layout()
    plot_path = plot_folder / outputs[i]
    plt.savefig(plot_path, dpi=150)
    plt.close()
    print(f"Saved {plot_path}")
    print(names[i] + ": " + str(round(duration, 2)) + " seconds, " + str(fs) + " samples/second")