"""
analysis.py - feature extraction for each song (the "listen" stage).

Everything here works on one song at a time. scoring.py then compares two songs.

DSP tools used in this file
  Sampling ............... decode to 22,050 Hz mono, 512-sample hop (23 ms frames)
  Frequency domain ....... STFT (4096-pt Hann), Fourier tempogram
  Spectral flux .......... onset detection (drum hits / note starts)
  Comb-filter search ..... beat and downbeat tracking
  Different basis ........ chroma (12 pitch classes)
  Key templates .......... Krumhansl-Schmuckler major/minor profiles
  Band energy / RMS ...... spectrum and loudness features
"""
import subprocess
import numpy as np
from scipy import signal

SR = 22050          # analysis sample rate (Hz)
HOP = 512           # STFT hop (samples) -> 23 ms frames
NFFT = 4096         # STFT window length (samples)
FPS = SR / HOP      # frames per second of every envelope (~43 Hz)

NOTE = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
KMAJ = np.array([6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88])  # Krumhansl major
KMIN = np.array([6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17])  # Krumhansl minor
BAND_EDGES = [20, 60, 120, 250, 500, 1000, 2000, 4000, 8000]                                 # Hz

CAMELOT = {('B', 'major'): '1B', ('F#', 'major'): '2B', ('C#', 'major'): '3B', ('G#', 'major'): '4B',
           ('D#', 'major'): '5B', ('A#', 'major'): '6B', ('F', 'major'): '7B', ('C', 'major'): '8B',
           ('G', 'major'): '9B', ('D', 'major'): '10B', ('A', 'major'): '11B', ('E', 'major'): '12B',
           ('G#', 'minor'): '1A', ('D#', 'minor'): '2A', ('A#', 'minor'): '3A', ('F', 'minor'): '4A',
           ('C', 'minor'): '5A', ('G', 'minor'): '6A', ('D', 'minor'): '7A', ('A', 'minor'): '8A',
           ('E', 'minor'): '9A', ('B', 'minor'): '10A', ('F#', 'minor'): '11A', ('C#', 'minor'): '12A'}


# ----------------------------------------------------------------------------- sampling
def load_mono(path):
    """Decode any audio file (mp3, wav, ...) to mono float samples at SR using ffmpeg."""
    cmd = ['ffmpeg', '-loglevel', 'error', '-i', str(path), '-ac', '1', '-ar', str(SR), '-f', 's16le', '-']
    raw = subprocess.run(cmd, capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.int16).astype(np.float32) / 32768


# ----------------------------------------------------------------------------- frequency domain
def stft_mag(y):
    """Magnitude STFT: rows = frequency bins, columns = 23 ms frames."""
    f, _, Z = signal.stft(y, SR, nperseg=NFFT, noverlap=NFFT - HOP, boundary=None)
    S = np.abs(Z).astype(np.float32)
    return f, S


# ----------------------------------------------------------------------------- metric 1: tempo
def onset_envelope(S):
    """Spectral flux: sum of positive frame-to-frame increases of the log spectrum.
    Spikes on every drum hit or note start. A running median removes slow loudness changes."""
    L = np.log1p(S * 100)
    d = np.maximum(0, np.diff(L, axis=1)).sum(0)
    d = np.r_[0, d]
    d = d - signal.medfilt(d, 31)
    d = np.maximum(d, 0)
    return d / (d.max() + 1e-9)


def kick_envelope(f, S):
    """Same idea as onset_envelope but only on 30-150 Hz, used to find the downbeat (kick drum)."""
    low = np.maximum(0, np.diff(np.log1p(S[(f >= 30) & (f <= 150)] * 100), axis=1)).sum(0)
    return np.r_[0, low]


def tempogram(env, lo=60, hi=200):
    """Fourier tempogram: DFT of the onset envelope evaluated at lo..hi BPM (0.25 BPM steps).
    A steady beat is a peak; the 2nd harmonic is added (x0.5) to make the peak sharper."""
    e = env - env.mean()
    n = np.arange(len(e)) / FPS
    w = np.hanning(len(e))
    bpms = np.arange(lo, hi + .01, .25)
    mag = lambda bp: np.abs((e * w * np.exp(-2j * np.pi * bp / 60 * n)).sum())
    strength = np.array([mag(b) + .5 * mag(2 * b) for b in bpms])
    return bpms, strength / strength.max()


def beat_grid(env, kick_env, bpm, dur):
    """Comb-filter beat tracking: slide a comb of impulses (one per beat) across the onset
    envelope and keep the phase with the most energy. The downbeat is the beat (of 4) whose
    kick-band energy is highest. Returns beat times and downbeat times (s)."""
    p = 60 / bpm * FPS
    offs = np.arange(0, p, .25)
    k = np.arange(int((len(env) - p) / p))
    score = [np.interp(o + k * p, np.arange(len(env)), env).sum() for o in offs]
    phase = offs[int(np.argmax(score))] / FPS
    beats = phase + np.arange(int((dur - phase) / (60 / bpm))) * 60 / bpm
    kick = [np.interp(beats[i::4] * FPS, np.arange(len(kick_env)), kick_env).sum() for i in range(4)]
    return beats, beats[int(np.argmax(kick))::4]


# ----------------------------------------------------------------------------- metric 2: key
def chroma(f, S):
    """Change of basis: keep tonal spectral peaks (65-2100 Hz, > 4x local median) and fold each
    frequency into one of 12 pitch classes: pc = round(12*log2(f/440) + 69) mod 12."""
    m = (f >= 65) & (f <= 2100)
    pc = np.round(12 * np.log2(f[m] / 440) + 69).astype(int) % 12
    P = S[m] ** 2
    peaks = (P > np.roll(P, 1, 0)) & (P > np.roll(P, -1, 0)) & (P > 4 * signal.medfilt2d(P, (15, 1)))
    P = P * peaks
    C = np.zeros((12, S.shape[1]), np.float32)
    for i in range(12):
        C[i] = P[pc == i].sum(0)
    C = np.sqrt(C)
    return C / (C.max(0, keepdims=True) + 1e-9)


def key_profile_correlations(mean_chroma):
    """Correlation of the song's mean chroma with all 24 Krumhansl templates: 2 x 12 (major, minor)."""
    return np.array([[np.corrcoef(mean_chroma, np.roll(p, r))[0, 1] for r in range(12)] for p in (KMAJ, KMIN)])


def key_name(mean_chroma):
    """Best-matching key from the 24 templates: (correlation, 'F# minor', root index, 'minor')."""
    best = (-2, '')
    for r in range(12):
        for prof, q in ((KMAJ, 'major'), (KMIN, 'minor')):
            c = np.corrcoef(mean_chroma, np.roll(prof, r))[0, 1]
            if c > best[0]:
                best = (c, f'{NOTE[r]} {q}', r, q)
    return best


# ----------------------------------------------------------------------------- metric 3: spectrum
def band_energy(f, S):
    """STFT power summed into the 8 BAND_EDGES bands, per frame (8 x frames)."""
    return np.array([(S[(f >= lo) & (f < hi)] ** 2).mean(0) for lo, hi in zip(BAND_EDGES[:-1], BAND_EDGES[1:])])


# ----------------------------------------------------------------------------- metric 4: energy / structure
def rms_loudness(y):
    """RMS of 2048-sample windows every HOP samples (linear; convert with to_db)."""
    frames = np.lib.stride_tricks.sliding_window_view(y, 2048)[::HOP]
    return np.sqrt((frames ** 2).mean(1))


def to_db(x):
    return 20 * np.log10(x + 1e-4)


# ----------------------------------------------------------------------------- one call per song
def analyze_song(path):
    """Run every per-song measurement. Returns a dict used by scoring.py, render.py and export_matlab.py."""
    y = load_mono(path)
    dur = len(y) / SR
    f, S = stft_mag(y)
    env = onset_envelope(S)
    kick = kick_envelope(f, S)
    bpms, strength = tempogram(env)
    bpm = float(bpms[np.argmax(strength)])
    C = chroma(f, S)
    mc = C.mean(1)
    kconf, kname, kroot, kq = key_name(mc)
    B = band_energy(f, S)
    Blog = np.log1p(B * 1e3)
    Blog /= Blog.max(1, keepdims=True) + 1e-9
    return dict(path=str(path), y=y, dur=dur, f=f, S=S, env=env, kick=kick, tempo_bpms=bpms, tempo_strength=strength,
                bpm=bpm, C=C, mean_chroma_raw=mc, mean_chroma=mc / np.linalg.norm(mc), key=kname, keyroot=kroot,
                keyq=kq, keyconf=float(kconf), bands=B, features=np.vstack([C, Blog]), rms=rms_loudness(y))
