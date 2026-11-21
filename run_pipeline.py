#!/usr/bin/env python3
"""
run_pipeline.py - Song Transition System, full pipeline in one command.

    python run_pipeline.py SONG_A SONG_B [--out DIR] [--name-a "..."] [--name-b "..."] [--plots]

Song A plays first; song B comes in. Output folder:
    summary.json                      scores, decisions and top candidates
    transition_recommended.mp3/.wav   16 s of A + the fade (with bass swap) + 16 s of B
    transition_plain.mp3/.wav         same fade without the bass swap, for comparison
    handoff_1..3_*.mp3/.wav           the three best exit/entry pairs
    transition_data.mat               every DSP signal the MATLAB plots need
    transition_dsp_plots.m            the MATLAB plot script (copied here)
    figures/                          21 PNGs, created when you run the .m file (or use --plots)
"""
import argparse
import json
import shutil
import subprocess
from pathlib import Path

import numpy as np

from analysis import analyze_song
from scoring import plan_transition
from render import render_all, PRE
from export_matlab import export_mat

HERE = Path(__file__).resolve().parent


def mmss(t):
    return f'{int(t // 60)}:{int(round(t % 60)):02d}'


def mmss1(t):
    """m:ss.s, for fade times inside a clip"""
    return f'{int(t // 60)}:{t % 60:04.1f}'


def fade_timeline(tA, tB, xf, stretch):
    """When the fade happens: inside each output clip, and in each original song.
    B plays `stretch` times faster, so the fade covers xf*stretch seconds of the original B."""
    return dict(
        clip=dict(fade_start=mmss1(PRE), bass_swap=mmss1(PRE + xf / 2), fade_end=mmss1(PRE + xf),
                  clip_length=mmss1(2 * PRE + xf)),
        song_a=dict(fade_start=mmss1(tA), bass_swap=mmss1(tA + xf / 2), gone=mmss1(tA + xf)),
        song_b=dict(starts=mmss1(tB), bass_swap=mmss1(tB + xf / 2 * stretch), full_volume=mmss1(tB + xf * stretch)),
    )


def main():
    ap = argparse.ArgumentParser(description='Score two songs and build the transition between them.')
    ap.add_argument('song_a', help='first song (plays first)')
    ap.add_argument('song_b', help='second song (comes in)')
    ap.add_argument('--out', default='results', help='output folder (default: results)')
    ap.add_argument('--name-a', help='display name for song A (default: file name)')
    ap.add_argument('--name-b', help='display name for song B (default: file name)')
    ap.add_argument('--plots', action='store_true', help='also run the MATLAB/Octave plot script')
    args = ap.parse_args()

    out = Path(args.out); out.mkdir(parents=True, exist_ok=True)
    name_a = args.name_a or Path(args.song_a).stem
    name_b = args.name_b or Path(args.song_b).stem

    print('1/4 Listening: analyzing both songs ...')
    A = analyze_song(args.song_a)
    B = analyze_song(args.song_b)

    print('2/4 Planning: scoring the four metrics and searching exit/entry pairs ...')
    plan = plan_transition(A, B)

    print('3/4 Mixing: rendering the transition clips ...')
    rend = render_all(args.song_a, args.song_b, plan, out)

    print('4/4 Exporting data for MATLAB ...')
    export_mat(A, B, plan, rend, name_a, name_b, out / 'transition_data.mat')
    shutil.copy(HERE / 'transition_dsp_plots.m', out / 'transition_dsp_plots.m')

    s, w = plan['scores'], plan['weights']
    summary = dict(
        song_a=name_a, song_b=name_b, total=round(plan['total'], 3), mode=plan['mode'],
        scores={k: round(v, 3) for k, v in s.items()}, points={k: round(w[k] * s[k], 3) for k in w},
        tempo=dict(bpm_a=plan['bpmA'], bpm_b=plan['bpmB'], gap_pct=round(plan['gap'] * 100, 2),
                   stretch_b_pct=round((plan['stretch'] - 1) * 100, 2)),
        key=dict(key_a=plan['keyA'], key_b=plan['keyB'], camelot=[plan['camA'], plan['camB']],
                 confidence=[round(c, 2) for c in plan['keyconf']], shared_notes=plan['shared'],
                 pitch_shift_b_semitones=plan['shift'], correlation_by_shift=[round(x, 3) for x in plan['sims']]),
        spectrum=dict(bass_overlap_pct=round(plan['raw_clash'] * 100, 1), after_swap_pct=round(plan['post_clash'] * 100, 2)),
        cut=dict(exit_a=mmss(plan['tA']), enter_b=mmss(plan['tB']), crossfade_s=plan['xf'],
                 bass_swap_at_s=round(plan['xf'] / 2, 2), beat_offset_ms=rend['lag_ms']),
        top_candidates=[dict(exit_a=mmss(c['tA']), enter_b=mmss(c['tB']), score=round(c['score'], 3),
                             key=round(c['key'], 3), energy=round(c['energy'], 3)) for c in plan['candidates'][:6]],
        fade_timeline=fade_timeline(plan['tA'], plan['tB'], plan['xf'], plan['stretch']),
        top3=[dict(rank=k, file=h['file'], score=round(h['score'], 3), exit_a=mmss(h['tA']), enter_b=mmss(h['tB']),
                   **fade_timeline(h['tA'], h['tB'], plan['xf'], plan['stretch']))
              for k, h in enumerate(rend['handoffs'], 1)],
        sections_a=plan['sectionsA'], sections_b=plan['sectionsB'],
    )
    (out / 'summary.json').write_text(json.dumps(summary, indent=2, ensure_ascii=False))

    print(f"\n{name_a} -> {name_b}: score {plan['total']:.2f} / 1.00  ({plan['mode']} mode)")
    print(f"  tempo  {plan['bpmA']:.1f} vs {plan['bpmB']:.1f} BPM, B stretched {summary['tempo']['stretch_b_pct']:+.2f}%   +{w['tempo'] * s['tempo']:.2f}")
    print(f"  key    {plan['keyA']} vs {plan['keyB']}, B shifted {plan['shift']:+d} st   +{w['key'] * s['key']:.2f}")
    print(f"  spec   bass overlap {plan['raw_clash'] * 100:.0f}% -> {plan['post_clash'] * 100:.1f}% after swap   +{w['spec'] * s['spec']:.2f}")
    print(f"  energy exit {mmss(plan['tA'])} -> enter {mmss(plan['tB'])}   +{w['energy'] * s['energy']:.2f}")
    print(f"  fade   {plan['xf']} s, bass swap at {plan['xf'] / 2:.1f} s, beat offset {rend['lag_ms']:.0f} ms")
    ft = summary['fade_timeline']
    print(f"\nWhen the fade happens")
    print(f"  in each clip   fade starts {ft['clip']['fade_start']}, bass swap {ft['clip']['bass_swap']}, "
          f"fade ends {ft['clip']['fade_end']} (clip is {ft['clip']['clip_length']} long)")
    print(f"  in {name_a:<12s} fades out from {ft['song_a']['fade_start']} to {ft['song_a']['gone']} (bass leaves at {ft['song_a']['bass_swap']})")
    print(f"  in {name_b:<12s} fades in  from {ft['song_b']['starts']} to {ft['song_b']['full_volume']} (bass arrives at {ft['song_b']['bass_swap']})")
    print(f"\nTop {len(summary['top3'])} pairs (handoff clips, same fade)")
    for h in summary['top3']:
        print(f"  #{h['rank']} score {h['score']:.3f}  {h['file']}")
        print(f"       clip:  fade {h['clip']['fade_start']}-{h['clip']['fade_end']}, bass swap {h['clip']['bass_swap']}")
        print(f"       {name_a}: fades out {h['song_a']['fade_start']}-{h['song_a']['gone']}   "
              f"{name_b}: fades in {h['song_b']['starts']}-{h['song_b']['full_volume']}")
    print(f'\n  files  {out.resolve()}')

    if args.plots:
        run = None
        if shutil.which('matlab'):
            run = ['matlab', '-batch', 'transition_dsp_plots']
        elif shutil.which('octave'):
            run = ['octave', '--no-gui', '--eval', "run('transition_dsp_plots.m')"]
        if run:
            print('Running the plot script ...')
            subprocess.run(run, cwd=out, check=False)
        else:
            print('MATLAB/Octave not found: open the output folder in MATLAB and run transition_dsp_plots')


if __name__ == '__main__':
    main()  