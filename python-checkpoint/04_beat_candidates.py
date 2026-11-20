# This is a first attempt at finding possible beats, not a finished beat tracker.
# A strong peak can be a drum hit, another instrument, or part of a beat.
from pathlib import Path
import numpy as np
import soundfile as sf
import matplotlib.pyplot as plt
from scipy.signal import find_peaks

project_folder = Path(__file__).resolve().parent
audio_folder = project_folder / "audio"
output_folder = project_folder / "beginner_outputs"
output_folder.mkdir(exist_ok=True)

# We inspect the same original song sections as the other analysis plots.
song_names = ["Something Elated", "Night Owl"]
file_names = ["Something_Elated.mp3", "Night_Owl.mp3"]
start_times = [208, 0]
end_times = [232, 24]

figure, graphs = plt.subplots(2, 1, figsize=(11, 7), constrained_layout=True)

for song_number in range(2):
    # We read the song and average its left and right channels for analysis.
    audio, sample_rate = sf.read(audio_folder / file_names[song_number], always_2d=True)
    mono_audio = np.mean(audio, axis=1)
    start = start_times[song_number]
    end = end_times[song_number]
    clip = mono_audio[int(start * sample_rate):int(end * sample_rate)]
    if len(clip) != int(end * sample_rate) - int(start * sample_rate):
        raise ValueError("The selected section goes beyond the end of the song.")

    # We measure RMS in 0.02-second pieces to see short changes in signal level.
    samples_per_piece = int(0.02 * sample_rate)
    piece_duration = samples_per_piece / sample_rate
    levels = []
    times = []
    for beginning in range(0, len(clip) - samples_per_piece + 1, samples_per_piece):
        piece = clip[beginning:beginning + samples_per_piece]
        levels.append(np.sqrt(np.mean(piece ** 2)))
        times.append(start + (beginning + samples_per_piece / 2) / sample_rate)
    levels = np.array(levels)
    times = np.array(times)

    # We keep peaks separated by at least 0.25 seconds to avoid very close peaks.
    # Prominence measures how much a peak stands out above its surroundings.
    # These are trial settings, not a known tempo or a claim about the music.
    minimum_distance = int(np.ceil(0.25 / piece_duration))
    minimum_prominence = 0.10 * np.max(levels)
    peaks, properties = find_peaks(levels, distance=minimum_distance,
                                  prominence=minimum_prominence)
    peak_times = times[peaks]

    # If every selected peak were one beat, this would estimate the tempo.
    # Real peaks can be missed or extra, so this number needs a listening check.
    if len(peaks) >= 3:
        gaps = np.diff(peak_times)
        candidate_rate = 60 / np.median(gaps)
        print(song_names[song_number] + ": " + str(len(peaks)) + " candidate peaks")
        print("Unverified peak-spacing rate: " + str(round(candidate_rate, 1)) + " per minute")
        print("Gap range: " + str(round(min(gaps), 2)) + " to " + str(round(max(gaps), 2)) + " seconds")
        print("The gaps vary. Do not report this as confirmed song BPM.\n")
    else:
        print(song_names[song_number] + ": too few peaks to estimate spacing.")

    graph = graphs[song_number]
    graph.plot(times, levels, color="darkblue", label="RMS signal level")
    graph.plot(peak_times, levels[peaks], "rx", label="Possible beats (peak candidates)")
    graph.set_title(song_names[song_number])
    graph.set_xlabel("Time in the original song (seconds)")
    graph.set_ylabel("RMS signal level")
    graph.set_xlim(start, end)
    graph.set_ylim(bottom=0)
    graph.legend(loc="upper right", fontsize=9)
    graph.grid(alpha=0.2)

figure.suptitle("Beat candidates: which signal peaks might follow the rhythm?")
figure.savefig(output_folder / "04_beat_candidates.png", dpi=150)
plt.close(figure)
print("Saved beginner_outputs/04_beat_candidates.png")
# SciPy reference: https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.find_peaks.html
