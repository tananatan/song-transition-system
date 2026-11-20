# I use an FFT to see which frequencies are strongest in a song or excerpt.
from pathlib import Path

import numpy as np
import soundfile as sf
import matplotlib.pyplot as plt
from scipy.fft import rfft, rfftfreq
from scipy.signal.windows import hann

from plot_excerpts import SONGS, website_excerpt, website_requested

# Website figures use their own output folder and 20-second excerpts.
website = website_requested()
folder = Path(__file__).resolve().parent
plot_folder = folder / ("website_plots" if website else "plots")
plot_folder.mkdir(exist_ok=True)

outputs = ["Something_Elated_full_fft.png", "Night_Owl_full_fft.png"]

def one_sided_fft(audio, fs, window=None):
    sample_count = len(audio)
    scale = sample_count
    if window is not None:
        # The Hann window tapers the edges. Its sum corrects for the change in amplitude.
        audio = audio * window
        scale = window.sum()

    # rfft keeps the zero and positive frequencies. rfftfreq gives their positions in Hz.
    spectrum = rfft(audio)
    frequencies = rfftfreq(sample_count, d=1 / fs)
    amplitude = np.abs(spectrum) / scale
    # We include the matching negative-frequency contribution in this one-sided plot.
    # Zero frequency and the Nyquist bin (when present) must not be doubled.
    if sample_count % 2 == 0:
        amplitude[1:-1] = 2 * amplitude[1:-1]
    else:
        amplitude[1:] = 2 * amplitude[1:]

    return frequencies, amplitude


if website:
    figure, axes = plt.subplots(2, 1, figsize=(10, 7), sharex=True, sharey=True,
                                layout="constrained")
    figure.suptitle("20-second spectrum")
    for axis, (filename, name, role) in zip(axes, SONGS):
        audio, fs = sf.read(folder / filename)
        audio = np.mean(audio, axis=1)
        clip, start, end = website_excerpt(audio, fs, role)
        window = hann(len(clip), sym=False)
        frequencies, amplitude = one_sided_fft(clip, fs, window)
        # I use the same 1-unit reference and axes so I can compare the two spectra.
        level = 20 * np.log10(np.maximum(amplitude, 1e-6))
        axis.plot(frequencies, level, linewidth=0.5)
        axis.set_title(f"{name} ({role}), {start:.2f} to {end:.2f} s")
        axis.set_xlim(0, fs / 2)
        axis.set_ylim(-120, -20)
        axis.set_ylabel("FFT magnitude (dB re 1)")
    axes[-1].set_xlabel("Frequency (Hz)")
    plot_path = plot_folder / "05_20_second_spectrum.png"
    figure.savefig(plot_path, dpi=150)
    plt.close(figure)
    print(f"Saved {plot_path}")

else:
    for (filename, name, role), output in zip(SONGS, outputs):
        # I use the full recording for the archived spectrum.
        audio, fs = sf.read(folder / filename, dtype="float32")
        audio = np.mean(audio, axis=1)
        sample_count = len(audio)
        frequencies, amplitude = one_sided_fft(audio, fs)

        plt.figure(figsize=(10, 5))
        plt.plot(frequencies, amplitude, linewidth=0.5)
        plt.xlim(0, fs / 2)
        plt.ylim(bottom=0)
        plt.xlabel("Frequency (Hz)")
        plt.ylabel("One-sided FFT amplitude")
        plt.title(name + ": FFT of the whole song")
        plt.tight_layout()
        plot_path = plot_folder / output
        plt.savefig(plot_path, dpi=150)
        plt.close()
        print(f"Saved {plot_path}")
        print(name + ": " + str(sample_count) + " samples; FFT spacing " + str(round(fs / sample_count, 5)) + " Hz")