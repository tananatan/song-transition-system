"""Preliminary song analysis. Run: python analyze_songs.py"""
from pathlib import Path
import json
import numpy as np
import soundfile as sf
from scipy import signal
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'outputs'
OUT.mkdir(exist_ok=True)
# Manually selected windows, not automatically optimized transition locations.
SONGS = [('Something Elated', 'Something_Elated.mp3', 208, 232),
         ('Night Owl', 'Night_Owl.mp3', 0, 24)]

def clock_label(seconds, position=None):
    return f'{int(seconds)//60}:{int(seconds)%60:02d}'

def time_axis(ax):
    ax.xaxis.set_major_formatter(FuncFormatter(clock_label))
    ax.set_xlabel('Original song time (min:sec)')
    ax.grid(alpha=0.2)

plt.rcParams.update({'font.size': 11, 'axes.spines.top': False,
                     'axes.spines.right': False})
wave_fig, wave_axes = plt.subplots(2, 1, figsize=(11, 7), constrained_layout=True)
beat_fig, beat_axes = plt.subplots(2, 1, figsize=(11, 7), constrained_layout=True)
freq_fig, freq_axes = plt.subplots(2, 1, figsize=(11, 7), constrained_layout=True)
summary = []

for row, (title, filename, start, end) in enumerate(SONGS):
    stereo, fs = sf.read(ROOT / 'audio' / filename, always_2d=True)
    # Mono is for analysis only; this script does not render a transition.
    full = stereo.mean(axis=1)
    x = full[int(start*fs):int(end*fs)]
    assert len(x) == (end-start)*fs and np.isfinite(x).all()
    t = start + np.arange(len(x)) / fs

    # 50 ms RMS measures signal level, not perceptual loudness (LUFS).
    frame = int(0.05*fs)
    frames = x[:len(x)//frame*frame].reshape(-1, frame)
    rms = np.sqrt(np.mean(frames**2, axis=1))
    rms_t = start + (np.arange(len(rms))+0.5)*frame/fs
    ax = wave_axes[row]
    ax.plot(t[::100], x[::100], color='#bccbd7', linewidth=0.5, label='Mono waveform (display decimated)')
    ax.plot(rms_t, rms, color='#174e74', linewidth=1.5, label='50 ms RMS level')
    ax.set(title=title, ylabel='Amplitude / RMS', ylim=(-1, 1), xlim=(start,end))
    time_axis(ax)
    ax.legend(loc='upper right', fontsize=9)

    # Short-time Fourier transform: same settings for both songs.
    f, st, z = signal.stft(x, fs, nperseg=2048, noverlap=1536, boundary=None, padded=False)
    magnitude = np.abs(z)
    # Spectral flux: increases in spectral magnitude indicate possible attacks.
    flux = np.maximum(np.diff(magnitude, axis=1), 0).sum(axis=0)
    flux = flux / max(flux.max(), 1e-12)
    flux_t = start + st[1:]
    dt = 512/fs
    peaks, _ = signal.find_peaks(flux, distance=int(0.20/dt), prominence=0.12)

    # Autocorrelation suggests repeated periods. It does NOT verify musical beats.
    centered = flux - flux.mean()
    ac = signal.correlate(centered, centered, mode='full', method='fft')[len(flux)-1:]
    ac = ac / max(ac[0], 1e-12)
    lags, _ = signal.find_peaks(ac)
    lags = [lag for lag in lags if 60 <= 60/(lag*dt) <= 180]
    lags = sorted(lags, key=lambda lag: ac[lag], reverse=True)[:3]
    candidates = [{'bpm': round(60/(lag*dt),1), 'correlation': round(float(ac[lag]),3)} for lag in lags]
    ax = beat_axes[row]
    ax.plot(flux_t, flux, color='#584785', linewidth=1, label='Normalized spectral flux')
    ax.scatter(flux_t[peaks], flux[peaks], color='#c36529', s=12, label='Possible attacks, not verified beats')
    ax.set(title=f'{title}: candidate pulse rates '+', '.join(str(c['bpm']) for c in candidates)+' BPM',
           ylabel='Onset strength (relative)', xlim=(start,end), ylim=(0,1.15))
    time_axis(ax)
    ax.legend(loc='upper right', fontsize=8)

    # Show low/mid frequencies with identical color scale; no per-song scaling.
    db = 20*np.log10(np.maximum(magnitude, 1e-6))
    keep = f <= 4000
    ax = freq_axes[row]
    mesh = ax.pcolormesh(start+st, f[keep], db[keep], shading='auto', cmap='magma', vmin=-80, vmax=-10)
    ax.set(title=title, ylabel='Frequency (Hz)', xlim=(start,end))
    time_axis(ax)
    summary.append({'song':title, 'sample_rate':fs, 'duration_seconds':len(full)/fs,
                    'window_seconds':[start,end], 'mono_rms':float(np.sqrt(np.mean(x*x))),
                    'candidate_pulse_rates':candidates, 'attack_count':len(peaks)})

wave_fig.suptitle('1. Waveform and RMS level in the selected transition windows')
beat_fig.suptitle('2. Estimated rhythmic activity: listen to verify the beat')
freq_fig.suptitle('3. Frequency content over time: short-time Fourier transform')
freq_fig.colorbar(mesh, ax=list(freq_axes), label='STFT magnitude (dB re amplitude 1)')
for fig, name in [(wave_fig,'01_waveform_rms.png'),(beat_fig,'02_rhythm_candidates.png'),(freq_fig,'03_spectrogram.png')]:
    fig.savefig(OUT/name, dpi=160)
    plt.close(fig)
(OUT/'measurements.json').write_text(json.dumps(summary, indent=2))
print(json.dumps(summary, indent=2))
print('Saved three plots in', OUT)

