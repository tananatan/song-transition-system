# This script studies the original songs. It does not mix or change their audio.
from pathlib import Path
import numpy as np
import soundfile as sf
import matplotlib.pyplot as plt
from scipy import signal

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
    # The short-time Fourier transform measures frequencies in small overlapping pieces.
    # Each piece contains 2048 samples. Consecutive pieces share 1536 samples.
    frequencies, times, transform = signal.stft(
        clip, fs=sample_rate, nperseg=2048, noverlap=1536,
        boundary=None, padded=False
    )

    # Absolute value gives the strength of each frequency in each piece.
    strength = np.abs(transform)

    # Decibels make both weaker and stronger frequencies easier to see.
    # We avoid taking the logarithm of zero by setting a very small lower limit.
    safe_strength = np.maximum(strength, 0.000001)
    strength_db = 20 * np.log10(safe_strength)

    # We focus on frequencies up to 4000 Hz to keep this first graph readable.
    # This display limit does not mean the songs contain no higher frequencies.
    visible = frequencies <= 4000
    original_song_times = start + times
    colors = graph.pcolormesh(
        original_song_times, frequencies[visible], strength_db[visible],
        shading="auto", cmap="magma", vmin=-80, vmax=-10
    )
    graph.set_title(song_names[song_number])
    graph.set_xlabel("Time in the original song (seconds)")
    graph.set_ylabel("Frequency (Hz)")
    graph.set_xlim(start, end)

# Both songs use the same colors for the same strength so the comparison is fair.
figure.colorbar(colors, ax=graphs, label="Frequency strength (dB relative to amplitude 1)")
figure.suptitle("3. Frequency content: what might overlap during the transition?")
figure.savefig(output_folder / "03_frequency_content.png", dpi=150)
plt.close(figure)
print("Saved beginner_outputs/03_frequency_content.png")
