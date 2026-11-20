# This script studies the original songs. It does not mix or change their audio.
from pathlib import Path
import numpy as np
import soundfile as sf
import matplotlib.pyplot as plt

# These paths let the script find the audio even if Visual Studio starts elsewhere.
project_folder = Path(__file__).resolve().parent
audio_folder = project_folder / "audio"
output_folder = project_folder / "beginner_outputs"
output_folder.mkdir(exist_ok=True)

# These are manually chosen places to inspect, not automatically selected transitions.
song_names = ["Something Elated", "Night Owl"]
file_names = ["Something_Elated.mp3", "Night_Owl.mp3"]
start_times = [208, 0]
end_times = [232, 24]

# We put one song above the other so each graph has enough room to read.
figure, graphs = plt.subplots(2, 1, figsize=(10, 7), constrained_layout=True)

for song_number in range(2):
    # We read the audio and its sample rate, which is the samples per second.
    audio, sample_rate = sf.read(audio_folder / file_names[song_number], always_2d=True)

    # We average the left and right channels for this analysis only.
    mono_audio = np.mean(audio, axis=1)
    start = start_times[song_number]
    end = end_times[song_number]

    # A time in seconds becomes a sample number when multiplied by the sample rate.
    first_sample = int(start * sample_rate)
    last_sample = int(end * sample_rate)
    clip = mono_audio[first_sample:last_sample]
    if len(clip) != last_sample - first_sample:
        raise ValueError("The selected times go beyond the end of the song.")

    graph = graphs[song_number]
    # A single waveform sample cannot tell us how strong a whole passage is.
    # We measure the signal level in short 0.05-second pieces instead.
    samples_per_piece = int(0.05 * sample_rate)
    number_of_pieces = len(clip) // samples_per_piece
    levels = []
    times = []

    for piece_number in range(number_of_pieces):
        # We take the next complete piece of audio.
        beginning = piece_number * samples_per_piece
        ending = beginning + samples_per_piece
        piece = clip[beginning:ending]

        # RMS means square the samples, average them, and take the square root.
        # Squaring stops positive and negative samples from canceling each other.
        squared_samples = piece ** 2
        average_square = np.mean(squared_samples)
        rms_level = np.sqrt(average_square)
        levels.append(rms_level)

        # We plot each measurement at the middle of the piece it describes.
        middle_time = start + (beginning + samples_per_piece / 2) / sample_rate
        times.append(middle_time)

    # RMS is signal level, not an exact measure of perceived loudness.
    graph.plot(times, levels, color="darkblue")
    graph.set_title(song_names[song_number])
    graph.set_xlabel("Time in the original song (seconds)")
    graph.set_ylabel("RMS signal level")
    graph.set_xlim(start, end)
    graph.set_ylim(0, 0.7)
    graph.grid(alpha=0.2)

figure.suptitle("2. Signal level: where is there room for the next song?")
figure.savefig(output_folder / "02_signal_level.png", dpi=150)
plt.close(figure)
print("Saved beginner_outputs/02_signal_level.png")
