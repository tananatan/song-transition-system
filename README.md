# Song Transition System

EECS 351 Python project for analyzing two songs and finding possible points where they could overlap.

## Run the first plot

Use Python 3.14. From the repository root, install the dependencies in your Python environment.

```sh
python -m pip install -r requirements.txt
```

Create `analysis/audio/` and save these Broke For Free tracks there with the filenames shown.

- `Something_Elated.mp3` · [Download Something Elated](https://freemusicarchive.org/music/Broke_For_Free/Something_EP/Broke_For_Free_-_Something_EP_-_05_Something_Elated/) · [CC BY 3.0 US](https://creativecommons.org/licenses/by/3.0/us/)
- `Night_Owl.mp3` · [Download Night Owl](https://freemusicarchive.org/music/Broke_For_Free/Directionless_EP/Broke_For_Free_-_Directionless_EP_-_01_Night_Owl/) · [CC BY 3.0](https://creativecommons.org/licenses/by/3.0/)

```sh
python analysis/01_waveform_loudness.py
```

Open `analysis/plots/01_waveform_loudness.png` to see the waveform and RMS signal level. Scripts `01` through `03` use the last 20% of **Something Elated** and first 20% of **Night Owl**. The frequency and beat plots help you inspect those regions. Scripts `04` and `05` plot the full recordings.

For the 20-second website plots, add `--website` when running scripts `01`, `02`, `03`, or `05`. Run `06_bass_energy.py` without a flag. These plots save to `analysis/website_plots/`.

## Rank possible cue pairs

```sh
python analysis/07_rank_cues.py
```

The script looks for beats within two seconds of the RMS drop near 229 s in **Something Elated** and pairs them with beats in the first 20% of **Night Owl**. The tempo estimates start from the plan's approximate 88 and 129 BPM. The script compares four seconds of audio for spectral similarity and uses a two-second overlap for bass, level, and harmony checks. You can change the quiet-spot time at the top of the script.

The score weights are spectral similarity (25%), bass clearance (25%), onset support (20%), level continuity (20%), and harmony (10%). The level score estimates the handoff using short RMS blocks. If any candidate has too little pitched sound, the script leaves harmony blank and rescales the other four weights for the whole run.

- `analysis/plots/top_cues.csv` lists the top three pairs, their times in the original songs, and their scores.
- `analysis/plots/cue_times.png` marks the highest-scoring pair on the two RMS plots.
