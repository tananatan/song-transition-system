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
#first number = something elated in sec, 
#second  number = night owel in seconds


#put one song above the other so each graph has enough room to read.
figure, graphs = plt.subplots(2, 1, figsize=(10, 7), constrained_layout=True)

#deals with each song individually 
for song_number in range(2):
    # We read the audio and its sample rate, which is the samples per second.
    audio, sample_rate = sf.read(audio_folder / file_names[song_number], always_2d=True)

    # We average the left and right channels for this analysis only.
    mono_audio = np.mean(audio, axis=1)
    start = start_times[song_number]
    end = end_times[song_number]

    # A time in seconds becomes a sample number when multiplied by the sample rate as covered in class 
    first_sample = int(start * sample_rate)
    last_sample = int(end * sample_rate)
    clip = mono_audio[first_sample:last_sample]
    if len(clip) != last_sample - first_sample:
        raise ValueError("The selected times go beyond the end of the song.")

    graph = graphs[song_number]
    # We give every audio sample its time in the original song.
    time = start + np.arange(len(clip)) / sample_rate

    # The waveform shows the signal moving above and below zero.
    graph.plot(time, clip, color="steelblue", linewidth=0.4)
    graph.set_title(song_names[song_number])
    graph.set_xlabel("Time in the original song (seconds)")
    graph.set_ylabel("Signal amplitude")
    graph.set_xlim(start, end)
    graph.set_ylim(-1, 1)
    graph.grid(alpha=0.2)

figure.suptitle("1. Waveform: where does the signal become quieter or busier?")
figure.savefig(output_folder / "01_waveform.png", dpi=150)
plt.close(figure)
print("Saved beginner_outputs/01_waveform.png")
