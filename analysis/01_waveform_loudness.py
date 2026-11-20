# Plot the waveform and its RMS level for the end of A and the start of B.
import matplotlib.pyplot as plt
import numpy as np

from plot_excerpts import (
    ANALYSIS_FOLDER, SONGS, load_song, set_excerpt_axis, short_time_rms,
    song_excerpt, website_requested,
)

# Set up the output folder and pick the clip length.
website = website_requested()
excerpt_seconds = 20 if website else None
plot_folder = ANALYSIS_FOLDER / ("website_plots" if website else "plots")
plot_folder.mkdir(exist_ok=True)

# Put the outgoing song above the incoming song.
figure, axes = plt.subplots(2, 1, figsize=(10, 7), layout="constrained")
if website:
    figure.suptitle("20-second waveform and RMS level")
for axis, (filename, name, role) in zip(axes, SONGS):
    # Read the mono audio and select the cue-search or website section.
    audio, fs = load_song(filename)
    clip, start, end = song_excerpt(audio, fs, role, excerpt_seconds)

    # Plot each sample in blue and the RMS level of each 50 ms block in orange.
    sample_times = start + np.arange(len(clip)) / fs
    rms_times, rms = short_time_rms(clip, fs)
    axis.plot(sample_times, clip, linewidth=0.5, label="Waveform")
    axis.plot(start + rms_times, rms, color="orange", label="RMS level")

    # Label both traces with times from the beginning of the original song.
    axis.set_title(f"{name} ({role})")
    axis.set_ylim(-1.05, 1.05)
    axis.set_ylabel("Signal amplitude / RMS level")
    axis.legend()
    if website:
        set_excerpt_axis(axis, start, end)
    else:
        axis.set_xlim(start, end)
        axis.set_xlabel("Time in the original song (seconds)")

# Save a PNG that can be opened in VS Code.
plot_path = plot_folder / ("01_waveform_rms.png" if website else "01_waveform_loudness.png")
figure.savefig(plot_path, dpi=150)
plt.close(figure)
print(f"Saved {plot_path}")
