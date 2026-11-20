# Rank possible places to start the overlap using measurements from the two songs.
import csv

import librosa
import matplotlib.pyplot as plt
import numpy as np
from scipy.signal import stft

from plot_excerpts import (
    ANALYSIS_FOLDER, BEAT_HOP, SONGS, find_beats, load_song, short_time_rms, song_excerpt,
)


# Start near the RMS drop we observed in Something Elated.
# These lengths are for two different comparisons.
QUIET_SPOT_SECONDS = 229
NEAR_QUIET_SPOT_SECONDS = 2
REFERENCE_SECONDS = 4
OVERLAP_SECONDS = 2
SILENCE_RMS = 0.01
FFT_SIZE = 4096
HOP_SIZE = 512
MIN_HARMONIC_SHARE = 0.20
WEIGHTS = {"spectral": 25, "bass": 25, "onset": 20, "level": 20, "harmony": 10}


def clip_spectrum(clip, fs):
    # Use the same Hann window, FFT size, and hop for both songs.
    frequencies, _, spectrum = stft(
        clip, fs=fs, window="hann", nperseg=FFT_SIZE,
        noverlap=FFT_SIZE - HOP_SIZE, boundary=None, padded=False,
    )
    return frequencies, np.abs(spectrum)


def spectral_balance(clip, fs):
    # Find the share of power in bass, mids, and highs. Each bin belongs to one band.
    frequencies, magnitude = clip_spectrum(clip, fs)
    power = (magnitude ** 2).mean(axis=1)
    bass = power[(frequencies >= 30) & (frequencies < 250)].sum()
    mids = power[(frequencies >= 250) & (frequencies < 2000)].sum()
    highs = power[frequencies >= 2000].sum()
    bands = np.array([bass, mids, highs])

    total_power = bands.sum()
    if total_power <= 1e-12:
        return None
    return bands / total_power


def overlap_features(clip, fs):
    # Track bass power and RMS level through the proposed overlap.
    frequencies, magnitude = clip_spectrum(clip, fs)
    bass_band = (frequencies >= 30) & (frequencies < 250)
    bass = (magnitude[bass_band] ** 2).sum(axis=0)
    _, rms = short_time_rms(clip, fs)
    level_db = 20 * np.log10(np.maximum(rms, 1e-6))

    # Separate pitched sound from percussive sound before comparing the 12 notes.
    harmonic, _ = librosa.decompose.hpss(magnitude)
    harmonic_power = harmonic ** 2
    chroma = None
    if harmonic_power.sum() > MIN_HARMONIC_SHARE * (magnitude ** 2).sum():
        notes = librosa.feature.chroma_stft(
            S=harmonic_power, sr=fs, n_fft=FFT_SIZE, tuning=0,
        ).mean(axis=1)
        note_length = np.linalg.norm(notes)
        if note_length > 0:
            # Unit-length note profiles can be compared with a dot product.
            chroma = notes / note_length

    return {"bass": bass, "level_db": level_db, "chroma": chroma}


def level_score(level_a, level_b):
    # Estimate the handoff using A at the start, the louder track through the
    # overlap, and B at the end. Using medians keeps one peak from deciding the score.
    louder = np.maximum(level_a, level_b)
    levels = [np.median(level_a[:4])]
    for section in np.array_split(louder, 3):
        levels.append(np.median(section))
    levels.append(np.median(level_b[-4:]))
    largest_jump = np.max(np.abs(np.diff(levels)))
    return max(0.0, 1 - largest_jump / 20)


def save_cue_plot(regions, cues, fs, path):
    # Mark the highest-scoring times on the RMS plots for the two search regions.
    figure, axes = plt.subplots(2, 1, figsize=(10, 6), sharey=True, layout="constrained")
    figure.suptitle("Highest-scoring cue pair")
    for axis, (clip, start, end), (_, name, role), cue in zip(axes, regions, SONGS, cues):
        times, rms = short_time_rms(clip, fs)
        axis.plot(start + times, rms)
        axis.axvline(cue, color="tab:red", linestyle="--")
        axis.set_xlim(start, end)
        axis.set_ylim(bottom=0)
        axis.set_title(f"{name} ({role}), cue at {cue:.2f} s")
        axis.set_xlabel("Time in original song (seconds)")
        axis.set_ylabel("RMS level")
    figure.savefig(path, dpi=150)
    plt.close(figure)


def main():
    # Read the two songs at their original sample rate and find beats in the cue regions.
    audio_a, fs = load_song(SONGS[0][0])
    audio_b, fs_b = load_song(SONGS[1][0])
    if fs != fs_b:
        raise SystemExit("Use recordings with the same sample rate to compare cues.")
    region_a = song_excerpt(audio_a, fs, "outgoing")
    region_b = song_excerpt(audio_b, fs, "incoming")
    tempo_a, frames_a, _ = find_beats(region_a[0], fs, "outgoing")
    tempo_b, frames_b, onsets_b = find_beats(region_b[0], fs, "incoming")
    start_a = round(region_a[1] * fs)
    print(f"Beat estimates   Something Elated {tempo_a:.1f} BPM   Night Owl {tempo_b:.1f} BPM")

    # Take one fixed four-second reference before A's quiet spot.
    reference_samples = round(REFERENCE_SECONDS * fs)
    overlap_samples = round(OVERLAP_SECONDS * fs)
    quiet_sample = round(QUIET_SPOT_SECONDS * fs)
    if not start_a + reference_samples <= quiet_sample <= len(audio_a):
        raise SystemExit("Pick a quiet spot with four seconds of audio before it in A's search region.")
    reference = audio_a[quiet_sample - reference_samples:quiet_sample]
    reference_bands = spectral_balance(reference, fs)
    if reference_bands is None or np.sqrt(np.mean(reference ** 2)) < SILENCE_RMS:
        raise SystemExit("A's four-second reference is too quiet. Choose a different quiet spot.")

    # Keep nearby beats in A with enough samples left for the whole overlap.
    candidates_a = {}
    for frame in frames_a:
        cue = start_a + frame * BEAT_HOP
        if abs(cue - quiet_sample) > NEAR_QUIET_SPOT_SECONDS * fs:
            continue
        overlap = audio_a[cue:cue + overlap_samples]
        if len(overlap) == overlap_samples:
            candidates_a[cue] = overlap_features(overlap, fs)

    # Check B's early beats. Skip silent entrances and clips that run past the end.
    candidates_b = {}
    comparison_samples = max(reference_samples, overlap_samples)
    onset_radius = round(0.05 * fs / BEAT_HOP)
    onset_peak = max(onsets_b.max(), 1e-12)
    for frame in frames_b:
        cue = frame * BEAT_HOP
        clip = audio_b[cue:cue + comparison_samples]
        if len(clip) != comparison_samples:
            continue
        first_samples = clip[:round(0.1 * fs)]
        if np.sqrt(np.mean(first_samples ** 2)) < SILENCE_RMS:
            continue
        bands = spectral_balance(clip[:reference_samples], fs)
        if bands is None:
            continue

        # Save the band match and the strongest attack within 50 ms of this beat.
        features = overlap_features(clip[:overlap_samples], fs)
        distance = np.abs(reference_bands - bands).sum()
        features["spectral"] = np.clip(1 - 0.5 * distance, 0, 1)
        nearby_onsets = onsets_b[max(0, frame - onset_radius):frame + onset_radius + 1]
        features["onset"] = nearby_onsets.max() / onset_peak
        candidates_b[cue] = features

    if not candidates_a or not candidates_b:
        raise SystemExit("No cue pair fits. Check the beat plots and the quiet-spot setting.")

    # Use the same bass scale for all candidates. Use harmony only if every
    # candidate has enough pitched sound, so all pairs use the same weights.
    candidates = list(candidates_a.values()) + list(candidates_b.values())
    bass_frames = np.concatenate([candidate["bass"] for candidate in candidates])
    bass_reference = max(np.percentile(bass_frames, 95), 1e-12)
    weights = WEIGHTS.copy()
    if any(candidate["chroma"] is None for candidate in candidates):
        weights.pop("harmony")
        print("Harmony skipped for this run. The other scores are rescaled to 100.")
    weight_total = sum(weights.values())

    # Pair each A beat with each B beat and combine the scores out of 100.
    ranked = []
    for cue_a, a in candidates_a.items():
        for cue_b, b in candidates_b.items():
            shared_bass = np.minimum(a["bass"], b["bass"])
            bass_penalty = np.clip(shared_bass / bass_reference, 0, 1).mean()
            scores = {
                "spectral": b["spectral"],
                "bass": 1 - bass_penalty,
                "onset": b["onset"],
                "level": level_score(a["level_db"], b["level_db"]),
                "harmony": None,
            }
            if "harmony" in weights:
                scores["harmony"] = np.clip(a["chroma"] @ b["chroma"], 0, 1)
            total = 100 * sum(weights[key] * scores[key] for key in weights) / weight_total
            ranked.append({
                "cue_a_s": cue_a / fs, "cue_b_s": cue_b / fs,
                "overlap_s": OVERLAP_SECONDS, **scores, "score_100": total,
            })

    # Save the top three rows and plot the best pair on the original song axes.
    top = sorted(ranked, key=lambda row: row["score_100"], reverse=True)[:3]
    output = ANALYSIS_FOLDER / "plots"
    output.mkdir(exist_ok=True)
    csv_path = output / "top_cues.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(top[0]))
        writer.writeheader()
        for row in top:
            writer.writerow({
                name: f"{value:.3f}" if value is not None else "" for name, value in row.items()
            })
            print(f"A {row['cue_a_s']:.2f} s, B {row['cue_b_s']:.2f} s   {row['score_100']:.1f}/100")
    plot_path = output / "cue_times.png"
    best = top[0]
    save_cue_plot((region_a, region_b), (best["cue_a_s"], best["cue_b_s"]), fs, plot_path)
    print(f"Saved {csv_path} and {plot_path}")


if __name__ == "__main__":
    main()
