"""
scoring.py - compare two analyzed songs and plan the transition (the "plan" stage).

  Metric 1  Tempo      (weight 0.35)  tempo gap, half/double time, 8% stretch limit -> blend or bridge
  Metric 2  Key        (weight 0.30)  chroma correlation, circular-shift search (pitch shift up to +-2 st)
  Metric 3  Spectrum   (weight 0.20)  bass-band overlap, left over after the 400 Hz Butterworth swap
  Metric 4  Energy /   (weight 0.15)  self-similarity matrix, checkerboard novelty, loudness match
            structure
  Then: phrase-aligned candidate search (every 8-bar exit in A x every 8-bar entry in B), weighted score.
"""
import numpy as np
from scipy import signal
from analysis import SR, FPS, NOTE, BAND_EDGES, CAMELOT, beat_grid, to_db

WEIGHTS = dict(tempo=.35, key=.30, spec=.20, energy=.15)
STRETCH_LIMIT = .08       # max tempo gap for a blend (8%)
MAX_PITCH_SHIFT = 2       # semitones
SHIFT_PENALTY = .03       # score cost per semitone of pitch shift
SPLIT_HZ = 400            # bass / highs crossover for the bass swap


def block_average(F, blk):
    """Average feature frames into blocks of blk frames (~1 s)."""
    nb = F.shape[1] // blk
    return F[:, :nb * blk].reshape(F.shape[0], nb, blk).mean(2)


def normalize_cols(F):
    """Remove each feature's mean, then scale each column to unit length (for cosine similarity)."""
    F = F - F.mean(1, keepdims=True)
    return F / (np.linalg.norm(F, axis=0, keepdims=True) + 1e-9)


def checkerboard_kernel(L=8):
    """16x16 kernel: +1 on the diagonal quadrants, -1 off them, Gaussian taper."""
    k = np.ones((2 * L, 2 * L))
    k[:L, L:] = -1
    k[L:, :L] = -1
    g = signal.windows.gaussian(2 * L, L / 2)
    return k * np.outer(g, g)


def novelty_curve(M, L=8):
    """Image processing: slide the checkerboard kernel along the SSM diagonal (2D correlation).
    Peaks mark section boundaries."""
    k = checkerboard_kernel(L)
    P = np.pad(M, L, mode='edge')
    out = np.array([(P[i:i + 2 * L, i:i + 2 * L] * k).sum() for i in range(M.shape[0])])
    out = np.maximum(out, 0)
    return out / (out.max() + 1e-9)


def label_sections(nv, F, blk_sec, dur):
    """Cut at novelty peaks and give similar segments the same letter (Part A, B, ...)."""
    pk, _ = signal.find_peaks(nv, height=.25, distance=int(8 / blk_sec))
    bnd = [0] + [int(p) for p in pk if 4 / blk_sec < p < len(nv) - 4 / blk_sec] + [len(nv)]
    segs, means, letters = [], [], []
    Fz = normalize_cols(F)
    for a, b in zip(bnd[:-1], bnd[1:]):
        mu = Fz[:, a:b].mean(1)
        mu = mu / (np.linalg.norm(mu) + 1e-9)
        lab = next((l0 for m0, l0 in zip(means, letters) if float(mu @ m0) > .7), None)
        if lab is None:
            lab = chr(65 + len(set(letters)))
        means.append(mu)
        letters.append(lab)
        segs.append([round(a * blk_sec, 2), round(min(dur, b * blk_sec), 2), 'Part ' + lab])
    return segs


def plan_transition(A, B):
    """Score every metric and pick the best exit/entry pair. A, B = analysis.analyze_song() results."""
    # ---------------- metric 1: tempo (half / double time count as matches)
    ratio, gap = 1, 9.0
    for r in (1, 2, .5):
        g = abs(A['bpm'] - r * B['bpm']) / A['bpm']
        if g < gap:
            gap, ratio = g, r
    s_tempo = max(0.0, 1 - gap / STRETCH_LIMIT)
    mode = 'blend' if s_tempo > .05 else 'bridge'
    stretch = A['bpm'] / (ratio * B['bpm']) if mode == 'blend' else 1.0     # speed factor applied to B

    # ---------------- metric 2: key (centred cosine = correlation, circular shifts of B's chroma)
    cen = lambda v: (v - v.mean()) / (np.linalg.norm(v - v.mean()) + 1e-9)
    sims = [max(0.0, float(cen(A['mean_chroma']) @ cen(np.roll(B['mean_chroma'], s)))) for s in range(12)]
    signed = lambda s: s if s <= 6 else s - 12
    options = [(sims[s] - SHIFT_PENALTY * abs(signed(s)), s) for s in range(12) if abs(signed(s)) <= MAX_PITCH_SHIFT]
    key_global, shift = max(options)
    shift = signed(shift)
    if key_global - sims[0] < .10:                       # only shift when it clearly helps
        key_global, shift = sims[0], 0
    scale = lambda root, q: set((root + np.array([0, 2, 3, 5, 7, 8, 10] if q == 'minor' else [0, 2, 4, 5, 7, 9, 11])) % 12)
    shared = len(scale(A['keyroot'], A['keyq']) & scale(B['keyroot'], B['keyq']))

    # ---------------- metric 3: spectrum (bass overlap, then what the 400 Hz high-pass leaks)
    bandA = A['bands'].mean(1); bandA /= bandA.sum()
    bandB = B['bands'].mean(1); bandB /= bandB.sum()
    raw_clash = float(np.minimum(bandA[:3], bandB[:3]).sum() / max(bandA[:3].sum(), bandB[:3].sum()))
    sos_hp = signal.butter(4, SPLIT_HZ, 'high', fs=SR, output='sos')
    w, hh = signal.sosfreqz(sos_hp, worN=512, fs=SR)
    leak = float(np.mean(np.abs(hh[(w >= 20) & (w <= 250)]) ** 2))
    post_clash = raw_clash * leak
    s_spec = 1 - post_clash

    # ---------------- metric 4: structure (SSM + novelty) and the A x B cross-similarity
    blk = int(round(FPS)); blk_sec = blk / FPS
    FA, FB = block_average(A['features'], blk), block_average(B['features'], blk)
    MA, MB = normalize_cols(FA).T @ normalize_cols(FA), normalize_cols(FB).T @ normalize_cols(FB)
    nvA, nvB = novelty_curve(MA), novelty_curve(MB)
    FBs = FB.copy(); FBs[:12] = np.roll(FB[:12], shift % 12, axis=0)    # B's chroma after the pitch shift
    X = normalize_cols(FA).T @ normalize_cols(FBs)

    # ---------------- candidates: 8-bar phrase starts from the beat grid
    beatsA, downA = beat_grid(A['env'], A['kick'], A['bpm'], A['dur'])
    beatsB, downB = beat_grid(B['env'], B['kick'], B['bpm'], B['dur'])
    eA, eB = to_db(A['rms']), to_db(B['rms'])
    level = lambda e, t: float(np.mean(e[int(t * FPS):int((t + 4) * FPS)]))
    cands = []
    for ta in downA[::8]:
        i = int(ta / blk_sec)
        if ta < A['dur'] * .5 or ta > A['dur'] - 12 or i >= len(nvA):      # exit in A's 2nd half
            continue
        for tb in downB[::8]:
            j = int(tb / blk_sec)
            if tb > B['dur'] * .45 or j >= len(nvB):                         # entry in B's first 45%
                continue
            s_struct = .5 * max(nvA[max(0, i - 1):i + 2]) + .5 * max(nvB[max(0, j - 1):j + 2])
            s_energy = .5 * (1 - min(1, abs(level(eA, ta) - level(eB, tb)) / 12)) + .5 * s_struct
            s_key = .5 * key_global + .5 * max(0.0, float(X[min(i, X.shape[0] - 1), min(j, X.shape[1] - 1)]))
            score = WEIGHTS['tempo'] * s_tempo + WEIGHTS['key'] * s_key + WEIGHTS['spec'] * s_spec + WEIGHTS['energy'] * s_energy
            cands.append(dict(tA=float(ta), tB=float(tb), score=float(score), key=float(s_key), energy=float(s_energy)))
    if not cands:
        raise RuntimeError('No phrase-aligned exit/entry pairs found (songs too short?)')
    cands.sort(key=lambda c: -c['score'])
    best = cands[0]
    scores = dict(tempo=s_tempo, key=best['key'], spec=s_spec, energy=best['energy'])
    total = sum(WEIGHTS[k] * scores[k] for k in WEIGHTS)
    bar = 240 / A['bpm']
    xf = round(8 * bar, 2) if mode == 'blend' else round(min(8.0, 4 * bar), 2)   # crossfade length (s)

    return dict(
        mode=mode, ratio=ratio, gap=gap, stretch=stretch, bpmA=A['bpm'], bpmB=B['bpm'],
        keyA=A['key'], keyB=B['key'], camA=CAMELOT.get(tuple(A['key'].split())), camB=CAMELOT.get(tuple(B['key'].split())),
        keyconf=[A['keyconf'], B['keyconf']], sims=sims, shift=shift, shared=shared, key_global=key_global,
        keyB_after=NOTE[(B['keyroot'] + shift) % 12] + ' ' + B['keyq'],
        bandA=bandA, bandB=bandB, band_edges=BAND_EDGES, raw_clash=raw_clash, post_clash=post_clash,
        blk_sec=blk_sec, ssmA=MA, ssmB=MB, nvA=nvA, nvB=nvB, X=X,
        sectionsA=label_sections(nvA, FA, blk_sec, A['dur']), sectionsB=label_sections(nvB, FB, blk_sec, B['dur']),
        beatsA=beatsA, downA=downA, beatsB=beatsB, downB=downB,
        candidates=cands, tA=best['tA'], tB=best['tB'], xf=xf, scores=scores, total=total, weights=WEIGHTS,
    )
