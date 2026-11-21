"""
render.py - build the transition audio (the "mix" stage).

  1. Decode both songs at 44.1 kHz stereo. Song B is pitch-shifted (resampling) and
     time-stretched (WSOLA, ffmpeg atempo) according to the plan.
  2. Beat alignment: cross-correlate the two onset envelopes over the fade window,
     within +-half a beat, and shift B by the best lag.
  3. Split both songs at 400 Hz (4th-order Butterworth, zero phase with sosfiltfilt).
  4. Equal-power crossfade: gA = cos(pi t / 2), gB = sin(pi t / 2).
  5. Bass swap: A's bass for the first half, B's for the second, smoothed by a 250 ms boxcar.
  6. Save 16 s of A + the fade + 16 s of B as WAV and MP3.
"""
import subprocess
import wave
import numpy as np
from scipy import signal
from scipy.ndimage import uniform_filter1d

SR_OUT = 44100
HOP_ALIGN = 441            # 10 ms steps for the beat-alignment search
PRE = POST = 16.0          # seconds of each song around the fade in the clip


def decode_stereo(path, filt=None):
    cmd = ['ffmpeg', '-loglevel', 'error', '-i', str(path)] + (['-af', filt] if filt else []) + \
          ['-ac', '2', '-ar', str(SR_OUT), '-f', 'f32le', '-']
    raw = subprocess.run(cmd, capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).reshape(-1, 2).copy()


def song_b_filter(stretch, shift):
    """ffmpeg filter: pitch shift by resampling (asetrate), then WSOLA time-stretch (atempo)
    so the net speed change equals `stretch`."""
    if not shift:
        return f'atempo={stretch:.6f}'
    p = 2 ** (shift / 12)
    return f'asetrate={int(SR_OUT * p)},aresample={SR_OUT},atempo={stretch / p:.6f}'


def onset_44k(y):
    """Spectral-flux onset envelope at 10 ms resolution (same idea as analysis.onset_envelope)."""
    _, _, Z = signal.stft(y.mean(1), SR_OUT, nperseg=2048, noverlap=2048 - HOP_ALIGN, boundary=None)
    L = np.log1p(np.abs(Z) * 100)
    e = np.r_[0, np.maximum(0, np.diff(L, axis=1)).sum(0)]
    return e - e.mean()


def align_beats(yA, yB, a0, b0_nominal, n, beat_sec):
    """Linear systems: cross-correlation of the onset envelopes over the fade, lag within +-half a beat.
    Returns the best start sample in B, the lags (ms) and the normalized correlation curve."""
    eA = onset_44k(yA[a0:a0 + n])
    half = int(beat_sec / 2 * SR_OUT / HOP_ALIGN)
    lags, vals = [], []
    for L in range(-half, half + 1):
        b0 = b0_nominal + L * HOP_ALIGN
        eB = onset_44k(yB[b0:b0 + n])
        m = min(len(eA), len(eB))
        lags.append(L)
        vals.append(float((eA[:m] * eB[:m]).sum()))
    best = lags[int(np.argmax(vals))]
    curve = np.array(vals) / (np.abs(vals).max() + 1e-12)
    return b0_nominal + best * HOP_ALIGN, np.array(lags) * HOP_ALIGN / SR_OUT * 1000, curve


def crossfade(segA, segB, bass_swap=True, split_hz=400):
    """Equal-power crossfade, optionally with the 400 Hz bass swap at the midpoint."""
    n = len(segA)
    t = np.linspace(0, 1, n)[:, None]
    gA, gB = np.cos(np.pi / 2 * t), np.sin(np.pi / 2 * t)
    if not bass_swap:
        return gA * segA + gB * segB
    sos = signal.butter(4, split_hz, 'low', fs=SR_OUT, output='sos')
    lowA, lowB = signal.sosfiltfilt(sos, segA, axis=0), signal.sosfiltfilt(sos, segB, axis=0)
    # step (1 for the first half) convolved with a 250 ms boxcar, edges padded with their own value
    bassA = uniform_filter1d((t[:, 0] < .5).astype(float), int(.25 * SR_OUT), mode='nearest')[:, None]
    return gA * (segA - lowA + lowA * bassA) + gB * (segB - lowB + lowB * (1 - bassA))


def save_clip(path_stem, y):
    """Normalize, add a short fade-in/out, write WAV and MP3 (MP3 needs ffmpeg)."""
    y = y / np.max(np.abs(y)) * .95
    N = len(y)
    env = (np.minimum(1, np.arange(N) / (.3 * SR_OUT)) * np.minimum(1, (N - np.arange(N)) / (1.5 * SR_OUT)))[:, None]
    pcm = (y * env * 32767).astype(np.int16)
    with wave.open(f'{path_stem}.wav', 'wb') as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR_OUT); w.writeframes(pcm.tobytes())
    subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-i', f'{path_stem}.wav', '-b:a', '192k', f'{path_stem}.mp3'], check=True)


def mix_spectrogram(mix):
    """0-5 kHz spectrogram of the rendered fade, downsampled to 48 x 120 and scaled 0-1 (for the output-check plot)."""
    f, _, Z = signal.stft(mix.mean(1), SR_OUT, nperseg=4096, noverlap=4096 - 1024, boundary=None)
    S = 20 * np.log10(np.abs(Z[f <= 5000]) + 1e-5)
    rows = np.array_split(np.arange(S.shape[0]), 48)
    cols = np.array_split(np.arange(S.shape[1]), 120)
    M = np.array([[S[np.ix_(r, c)].mean() for c in cols] for r in rows])
    lo = np.percentile(M, 5)
    return np.clip((M - lo) / (M.max() - lo), 0, 1)


def render_all(pathA, pathB, plan, out_dir, n_handoffs=3):
    """Render the recommended clip, the plain-crossfade clip and the top-n handoff clips."""
    yA = decode_stereo(pathA)
    yB = decode_stereo(pathB, song_b_filter(plan['stretch'], plan['shift']))
    n = int(plan['xf'] * SR_OUT)
    beat = 60 / plan['bpmA']
    fmt = lambda t: f"{int(round(t) // 60)}m{int(round(t) % 60):02d}s"
    result = dict(handoffs=[])

    for k, c in enumerate(plan['candidates'][:n_handoffs], 1):
        a0 = int(c['tA'] * SR_OUT)
        if a0 < PRE * SR_OUT:
            raise RuntimeError('Exit point is too close to the start of song A for the 16 s lead-in')
        b0, lags_ms, curve = align_beats(yA, yB, a0, int(c['tB'] / plan['stretch'] * SR_OUT), n, beat)
        segA, segB = yA[a0:a0 + n], yB[b0:b0 + n]
        pre, post = yA[a0 - int(PRE * SR_OUT):a0], yB[b0 + n:b0 + n + int(POST * SR_OUT)]
        eq = crossfade(segA, segB, bass_swap=True)
        stem = f"handoff_{k}_exit_{fmt(c['tA'])}_enter_{fmt(c['tB'])}"
        save_clip(f'{out_dir}/{stem}', np.concatenate([pre, eq, post]))
        result['handoffs'].append(dict(file=stem + '.mp3', lag_ms=float(lags_ms[int(np.argmax(curve))]), **c))
        if k == 1:                                   # the winner also gets the plain version + analysis data
            save_clip(f'{out_dir}/transition_recommended', np.concatenate([pre, eq, post]))
            save_clip(f'{out_dir}/transition_plain', np.concatenate([pre, crossfade(segA, segB, bass_swap=False), post]))
            result.update(lag_ms=float(lags_ms[int(np.argmax(curve))]), xc_lag_ms=lags_ms, xc=curve,
                          mix_spec=mix_spectrogram(eq), clip_len=(len(pre) + n + len(post)) / SR_OUT)
    return result
