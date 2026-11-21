# Song Transition System
 
Takes two songs, scores how well they blend (0 to 1), picks where to cut, and renders the transition audio. It then exports every DSP step so MATLAB can plot it.
 
```
song A + song B
   │
   ├─ 1. Listen   analysis.py       per-song features (tempo, chroma/key, band energy, loudness)
   ├─ 2. Plan     scoring.py        4 weighted metrics + search for the best exit/entry pair
   ├─ 3. Mix      render.py         stretch/pitch-shift B, align beats, equal-power fade, bass swap
   └─ 4. Export   export_matlab.py  transition_data.mat  ──►  transition_dsp_plots.m  ──►  21 figures
```
 
## Requirements
 
| What | Notes |
|---|---|
| uv | Installs Python and the packages for you (step 1). |
| ffmpeg | Decodes the songs, time-stretches, pitch-shifts and writes the MP3s. Must be on your PATH (step 2). |
| MATLAB R2016b+ or GNU Octave 7+ | Only needed for the plots. Base MATLAB only, no toolboxes. |
 
## Run it step by step (with uv)
 
Example: **The Weeknd - São Paulo** fading into **Rihanna - We Found Love**.
 
### 1. Install uv (one time)
 
Mac or Linux:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```
 
Windows (PowerShell):
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```
 
Close and reopen the terminal, then check that it worked:
```bash
uv --version
```
 
### 2. Install ffmpeg (one time)
 
Mac:
```bash
brew install ffmpeg
```
 
Windows:
```powershell
winget install ffmpeg
```
 
Ubuntu:
```bash
sudo apt install ffmpeg
```
 
Close and reopen the terminal, then check:
```bash
ffmpeg -version
```
 
### 3. Put the MP3s in this folder
 
Copy both songs into the `song_transition` folder, next to `run_pipeline.py`:
 
```
song_transition/
├── run_pipeline.py
├── analysis.py
├── scoring.py
├── render.py
├── export_matlab.py
├── transition_dsp_plots.m
├── requirements.txt
├── The Weeknd - São Paulo (Official Audio).mp3              <- here
└── Rihanna - We Found Love (Audio) ft. Calvin Harris.mp3    <- here
```
 
### 4. Open a terminal in this folder
 
```bash
cd path/to/song_transition
```
 
On a Mac, type `cd ` and drag the folder into the terminal. On Windows, type `cmd` in the File Explorer address bar.
 
### 5. Set up Python and the packages (one time)
 
```bash
uv venv
uv pip install -r requirements.txt
```
 
`uv venv` creates a `.venv` folder with its own Python and downloads Python if you don't have it. The second command installs numpy and scipy into it.
 
### 6. Run the fade
 
Song A (plays first) comes first, song B (comes in) second:
 
```bash
uv run python run_pipeline.py "The Weeknd - São Paulo (Official Audio).mp3" "Rihanna - We Found Love (Audio) ft. Calvin Harris.mp3" --out results/sao_paulo --name-a "Sao Paulo" --name-b "We Found Love"
```
 
Keep the quotes, because the file names have spaces. It takes about 20–30 s and prints:
 
```
Sao Paulo -> We Found Love: score 0.68 / 1.00  (blend mode)
  tempo  129.0 vs 128.0 BPM, B stretched +0.78%   +0.32
  key    C major vs F# major, B shifted +2 st   +0.11
  spec   bass overlap 60% -> 0.1% after swap   +0.20
  energy exit 3:29 -> enter 1:31   +0.05
  fade   14.88 s, bass swap at 7.4 s, beat offset -20 ms
```
 
**"File not found"?** Some terminals (especially on Windows) mangle the "ã" in São. Rename the files to `saopaulo.mp3` and `wefoundlove.mp3`, then run:
 
```bash
uv run python run_pipeline.py saopaulo.mp3 wefoundlove.mp3 --out results/sao_paulo --name-a "Sao Paulo" --name-b "We Found Love"
```
 
### 7. Listen
 
Open `results/sao_paulo/` and play `transition_recommended.mp3`. It contains 16 s of São Paulo, the 14.9 s fade, then 16 s of We Found Love.
 
### 8. Make the MATLAB plots (optional)
 
```matlab
cd results/sao_paulo
transition_dsp_plots
```
 
The 21 PNGs are saved to `results/sao_paulo/figures/`. Or add `--plots` to the step 6 command, and it runs MATLAB (or Octave) for you if one is installed.
 
### Other song pairs
 
Use the same command with different files and a new `--out` folder:
 
```bash
uv run python run_pipeline.py "Best Part.mp3" "Nobody Gets Me.mp3" --out results/best_part --name-a "Best Part" --name-b "Nobody Gets Me"
```
 
### Without uv
 
With plain Python 3.9+ instead, run `pip install -r requirements.txt` once. Then run the step 6 command, starting with `python` instead of `uv run python`.
 
## Output folder
 
| File | What it is |
|---|---|
| `summary.json` | All scores, decisions (mode, stretch, pitch shift, cut points, beat offset), top 6 candidates, section labels |
| `transition_recommended.mp3` | 16 s of A + the fade with the bass swap + 16 s of B |
| `transition_plain.mp3` | Same fade without the bass swap, for comparison |
| `handoff_1..3_*.mp3` | The three best exit/entry pairs, same fade |
| `transition_data.mat` | Every intermediate DSP signal the plots use |
| `transition_dsp_plots.m` | The plot script (copied here so the folder is self-contained) |
| `figures/` | 21 PNGs, created by the plot script |
 
Each `.mp3` also has a `.wav` copy.
 
## Where each metric and DSP tool lives
 
| Metric (weight) | Code | DSP tools | Plots |
|---|---|---|---|
| Tempo (0.35) | `analysis.onset_envelope`, `tempogram`, `beat_grid`; `scoring` metric 1 | Sampling, STFT, spectral-flux onsets, Fourier tempogram, comb-filter beat tracking | m1a–m1d |
| Key (0.30) | `analysis.chroma`, `key_name`; `scoring` metric 2 | Spectral peak picking, chroma (change of basis), Krumhansl–Schmuckler templates, circular-shift correlation | m2a–m2d |
| Spectrum (0.20) | `analysis.band_energy`; `scoring` metric 3; `render.crossfade` | Band energy, 4th-order Butterworth LP/HP at 400 Hz, zero-phase filtering, convolution (bass ramp) | m3a–m3e |
| Energy and structure (0.15) | `analysis.rms_loudness`; `scoring.novelty_curve`, `plan_transition` | RMS framing, self-similarity matrix, checkerboard-kernel novelty (image processing) | m4a–m4d |
| Comparison and output | `scoring.plan_transition`; `render.align_beats`, `crossfade` | A×B cross-similarity, weighted grid search, cross-correlation beat alignment, WSOLA time-stretch, resampling pitch shift, equal-power fade | c1–c4 |
 
## Settings you can change
 
All are constants at the top of their file.
 
| Setting | File | Default | Effect |
|---|---|---|---|
| `WEIGHTS` | `scoring.py` | 0.35 / 0.30 / 0.20 / 0.15 | Importance of tempo / key / spectrum / energy |
| `STRETCH_LIMIT` | `scoring.py` | 0.08 | Largest tempo gap that still gets a blend (8%) |
| `MAX_PITCH_SHIFT`, `SHIFT_PENALTY` | `scoring.py` | 2 semitones, 0.03 per semitone | Pitch-shift limit and cost |
| `SPLIT_HZ` | `scoring.py` | 400 | Bass/highs crossover for the bass swap |
| `PRE`, `POST` | `render.py` | 16 s | Song A before and song B after the fade in each clip |
| Fade length | `scoring.py`, end of `plan_transition` | 8 bars (blend), up to 8 s (bridge) | Length of the crossfade |
 
## Limits to know
 
- **Meter is not scored.** The phrase grid assumes 4 beats per bar, so a 6/8 song (like Nobody Gets Me) can drift against a 4/4 song even when the BPM matches.
- **Key names are estimates.** Low confidence (under about 0.7) means the label may be off. The pitch-shift decision compares the chroma directly, so it doesn't rely on the label.
- **Cut-point rules:** the exit must fall in the second half of song A, and the entry in the first 45% of song B. Very short songs may have no valid pair, and the script stops with a message.
- **Copyright:** the clips contain parts of the original recordings. Keep them to class use.
## Troubleshooting
 
| Message | Fix |
|---|---|
| `FileNotFoundError: 'ffmpeg'` | Install ffmpeg and make sure `ffmpeg -version` works in the same terminal. |
| `No phrase-aligned exit/entry pairs found` | A song is too short, or the beat tracker found too few downbeats. Try longer songs. |
| `Exit point is too close to the start of song A` | Lower `PRE` in `render.py`. |
| MATLAB: `Unable to find file transition_data.mat` | Run `transition_dsp_plots` from inside the output folder (`cd` there first). |
 