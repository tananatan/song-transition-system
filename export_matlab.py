"""
export_matlab.py - save every intermediate DSP signal the MATLAB plots need to transition_data.mat.
"""
import numpy as np
from scipy import signal
from scipy.io import savemat
from scipy.ndimage import uniform_filter1d
from analysis import SR, HOP, NFFT, FPS, NOTE, KMAJ, KMIN, key_profile_correlations, to_db
from scoring import block_average, checkerboard_kernel, SPLIT_HZ


def export_mat(A, B, plan, rend, name_a, name_b, out_path):
    arr = lambda x: np.asarray(x, float)
    cell = lambda L: np.array(L, dtype=object)
    f = A['f']
    tA, tB, xf = plan['tA'], plan['tB'], plan['xf']

    # tempo / sampling views around the exit point
    a0 = int((tA - 2) * SR)
    wave_excerpt = A['y'][a0:a0 + 4 * SR]
    f0, f1 = int((tA - 4) * FPS), int((tA + 4) * FPS)
    fm = f <= 5000
    spec = 20 * np.log10(A['S'][fm][:, f0:f1][::2] + 1e-6)
    window = lambda X, t0: (X['env'][int((t0 - 4) * FPS):int((t0 + 4) * FPS)],
                            np.arange(int((t0 - 4) * FPS), int((t0 + 4) * FPS)) / FPS - t0)
    envA, envA_t = window(A, tA)
    envB, envB_t = window(B, tB)
    near = lambda v, t0: arr([x - t0 for x in v if abs(x - t0) <= 4])
    grid = np.arange(60, 201, 1.0)

    # key: one frame's tonal peaks + chroma over time + key templates
    fi = int(tA * FPS)
    km = (f >= 65) & (f <= 2100)
    P = A['S'][km] ** 2
    pk = (P > np.roll(P, 1, 0)) & (P > np.roll(P, -1, 0)) & (P > 4 * signal.medfilt2d(P, (15, 1)))
    frame_f = f[km]
    blk = int(round(FPS))

    # filters: response, poles/zeros, impulse/step, bass ramp
    sos_lp = signal.butter(4, SPLIT_HZ, 'low', fs=SR, output='sos')
    sos_hp = signal.butter(4, SPLIT_HZ, 'high', fs=SR, output='sos')
    z_lp, p_lp, _ = signal.butter(4, SPLIT_HZ, 'low', fs=SR, output='zpk')
    z_hp, p_hp, _ = signal.butter(4, SPLIT_HZ, 'high', fs=SR, output='zpk')
    wf = np.logspace(1, np.log10(SR / 2 * .98), 600)
    _, Hl = signal.sosfreqz(sos_lp, worN=wf, fs=SR)
    _, Hh = signal.sosfreqz(sos_hp, worN=wf, fs=SR)
    n = int(.03 * SR); imp = np.zeros(n); imp[0] = 1
    tt = np.linspace(0, xf, 1200)
    stepA = (tt < xf / 2).astype(float)
    k = int(.25 / (xf / 1200))
    pkA, _ = signal.find_peaks(plan['nvA'], height=.25, distance=int(8 / plan['blk_sec']))
    pkB, _ = signal.find_peaks(plan['nvB'], height=.25, distance=int(8 / plan['blk_sec']))
    rms_view = lambda X: np.round(np.convolve(to_db(X['rms'])[::8], np.ones(3) / 3, 'same'), 1)

    m = dict(
        songA=name_a, songB=name_b, sr=SR, hop=HOP, nfft=NFFT, fps=FPS, bpmA=plan['bpmA'], bpmB=plan['bpmB'],
        keyA=plan['keyA'], keyB=plan['keyB'],
        wave=arr(wave_excerpt), wave_t0=-2.0, spec=arr(spec), spec_f=arr(f[fm][::2]), spec_t=arr(np.arange(f0, f1) / FPS - tA),
        envA=arr(envA), envA_t=arr(envA_t), envB=arr(envB), envB_t=arr(envB_t),
        beatsA=near(plan['beatsA'], tA), downA=near(plan['downA'], tA), beatsB=near(plan['beatsB'], tB), downB=near(plan['downB'], tB),
        tempo_bpm=grid, tempo_A=np.interp(grid, A['tempo_bpms'], A['tempo_strength']),
        tempo_B=np.interp(grid, B['tempo_bpms'], B['tempo_strength']),
        frame_f=arr(frame_f), frame_mag=arr(20 * np.log10(A['S'][km, fi] + 1e-6)),
        frame_pk=arr(np.where(pk[:, fi])[0] + 1), frame_pc=arr(np.round(12 * np.log2(frame_f / 440) + 69).astype(int) % 12),
        chromA=arr(block_average(A['C'], blk)), chromB=arr(block_average(B['C'], blk)), blk_sec=plan['blk_sec'], notes=cell(NOTE),
        kcA=key_profile_correlations(A['mean_chroma']), kcB=key_profile_correlations(B['mean_chroma']),
        chromaA=arr(A['mean_chroma']), chromaB=arr(B['mean_chroma']), sims=arr(plan['sims']), shift=plan['shift'],
        band_edges=arr(plan['band_edges']), bandA=arr(plan['bandA']), bandB=arr(plan['bandB']),
        raw_clash=plan['raw_clash'], post_clash=plan['post_clash'],
        wf=wf, Hl=np.abs(Hl), Hh=np.abs(Hh), phl=np.unwrap(np.angle(Hl)), phh=np.unwrap(np.angle(Hh)),
        z_lp=np.c_[z_lp.real, z_lp.imag], p_lp=np.c_[p_lp.real, p_lp.imag], z_hp=np.c_[z_hp.real, z_hp.imag], p_hp=np.c_[p_hp.real, p_hp.imag],
        h_lp=signal.sosfilt(sos_lp, imp), s_lp=signal.sosfilt(sos_lp, np.ones(n)),
        ramp_t=tt, stepA=stepA, rampA=uniform_filter1d(stepA, k, mode='nearest'),
        rmsA=rms_view(A), rmsB=rms_view(B), rms_step=8 * HOP / SR, durA=A['dur'], durB=B['dur'],
        ssmA=np.round(plan['ssmA'], 2), ssmB=np.round(plan['ssmB'], 2), kern=checkerboard_kernel(8),
        nvA=arr(plan['nvA']), nvB=arr(plan['nvB']), pkA=arr(pkA + 1), pkB=arr(pkB + 1),
        X=np.round(plan['X'], 2), cands=arr([[c['tA'], c['tB'], c['key'], c['energy'], c['score']] for c in plan['candidates'][:6]]),
        xc_lag=arr(rend['xc_lag_ms']), xc=arr(rend['xc']), tA=tA, tB=tB, xf=xf, mix_spec=arr(rend['mix_spec']),
        scores=arr([plan['scores'][k] for k in ['tempo', 'key', 'spec', 'energy']]),
        weights=arr([plan['weights'][k] for k in ['tempo', 'key', 'spec', 'energy']]), total=plan['total'],
    )
    savemat(out_path, m, do_compression=True, oned_as='row')
