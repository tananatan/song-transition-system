# Use an FFT to see which frequencies are strongest in a song or excerpt.
import matplotlib.pyplot as plt
import numpy as np
from scipy.fft import rfft, rfftfreq
from scipy.signal.windows import hann

from song_tools import ANALYSIS_FOLDER, SONGS, load_song, song_excerpt, website_requested

# Choose where to save the FFT plots.
website = website_requested()
plot_folder = ANALYSIS_FOLDER / ("website_plots" if website else "plots")
plot_folder.mkdir(exist_ok=True)


# Measure the amplitude at each frequency. Both plot modes use this calculation.
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
    # Compare both 20-second excerpts on the same axes and dB scale.
    figure, axes = plt.subplots(2, 1, figsize=(10, 7), sharex=True, sharey=True,
                                layout="constrained")
    figure.suptitle("20-second spectrum")
    for axis, (filename, name, role) in zip(axes, SONGS):
        # Taper the edges of each excerpt before calculating its FFT.
        audio, fs = load_song(filename)
        clip, start, end = song_excerpt(audio, fs, role, seconds=20)
        window = hann(len(clip), sym=False)
        frequencies, amplitude = one_sided_fft(clip, fs, window)

        # Plot against a shared 1-unit amplitude reference for both songs.
        level = 20 * np.log10(np.maximum(amplitude, 1e-6))
        axis.plot(frequencies, level, linewidth=0.5)
        axis.set_title(f"{name} ({role}), {start:.2f} to {end:.2f} s")
        axis.set_xlim(0, fs / 2)
        axis.set_ylim(-120, -20)
        axis.set_ylabel("FFT magnitude (dB re 1)")

    # Save one figure with both excerpts.
    axes[-1].set_xlabel("Frequency (Hz)")
    plot_path = plot_folder / "05_20_second_spectrum.png"
    figure.savefig(plot_path, dpi=150)
    plt.close(figure)
    print(f"Saved {plot_path}")

else:
    for filename, name, _ in SONGS:
        # Use the full recording to show the overall frequency content.
        audio, fs = load_song(filename, dtype="float32")
        sample_count = len(audio)
        frequencies, amplitude = one_sided_fft(audio, fs)

        # Plot and save each whole-song spectrum on its own.
        plt.figure(figsize=(10, 5))
        plt.plot(frequencies, amplitude, linewidth=0.5)
        plt.xlim(0, fs / 2)
        plt.ylim(bottom=0)
        plt.xlabel("Frequency (Hz)")
        plt.ylabel("One-sided FFT amplitude")
        plt.title(name + ": FFT of the whole song")
        plt.tight_layout()
        plot_path = plot_folder / f"{name.replace(' ', '_')}_full_fft.png"
        plt.savefig(plot_path, dpi=150)
        plt.close()
        print(f"Saved {plot_path}")
        print(f"{name}: {sample_count} samples, FFT spacing {fs / sample_count:.5f} Hz")
