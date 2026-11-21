# Use librosa to estimate where the beats fall in each selected section.
import matplotlib.pyplot as plt

from song_tools import (
    ANALYSIS_FOLDER, BEAT_HOP, SONGS, find_beats, load_song, set_excerpt_axis,
    short_time_rms, song_excerpt, website_requested,
)

# Set up the output folder and pick the clip length.
website = website_requested()
excerpt_seconds = 20 if website else None
plot_folder = ANALYSIS_FOLDER / ("website_plots" if website else "plots")
plot_folder.mkdir(exist_ok=True)

# Give each song its own panel so the beat markers are easy to read.
figure, axes = plt.subplots(2, 1, figsize=(10, 7), layout="constrained")
if website:
    figure.suptitle("20-second rhythm and candidate beats")
for axis, (filename, name, role) in zip(axes, SONGS):
    # Measure the signal level in 20 ms blocks to show short changes.
    audio, fs = load_song(filename)
    clip, start, end = song_excerpt(audio, fs, role, excerpt_seconds)
    rms_times, rms = short_time_rms(clip, fs, seconds=0.02)

    # Use the wider cue-search region to estimate tempo for a short website plot.
    tempo_clip = None
    if website:
        tempo_clip, _, _ = song_excerpt(audio, fs, role)
    tempo_bpm, beat_frames, _ = find_beats(clip, fs, role, tempo_clip)
    clip_beat_times = beat_frames * BEAT_HOP / fs

    # Add the excerpt start to both traces so the plot uses original-song times.
    axis.plot(start + rms_times, rms, label="RMS signal level")
    axis.vlines(
        start + clip_beat_times, 0, rms.max(), colors="red", linestyles="dashed",
        alpha=0.5, label="Candidate beats",
    )
    axis.set_ylim(bottom=0)
    axis.set_title(f"{name} ({role}), {tempo_bpm:.1f} BPM estimate")
    axis.set_ylabel("RMS signal level")
    axis.legend()
    if website:
        set_excerpt_axis(axis, start, end)
    else:
        axis.set_xlim(start, end)
        axis.set_xlabel("Time in the original song (seconds)")
    print(f"{name}: {tempo_bpm:.1f} BPM estimate, {len(clip_beat_times)} candidate beats")

# Save the signal level and beat markers together.
plot_path = plot_folder / ("03_candidate_beats.png" if website else "03_librosa_beats.png")
figure.savefig(plot_path, dpi=150)
plt.close(figure)
print(f"Saved {plot_path}")
