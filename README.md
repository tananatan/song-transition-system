# Song Transition System

EECS 351 Python project for analyzing songs and choosing sections for a transition.

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

Open `analysis/plots/01_waveform_loudness.png` to see the waveform and signal level. Run scripts `02` through `05` the same way for spectrograms, beat estimates, and FFT plots.

For the 20-second website plots, add `--website` when running scripts `01`, `02`, `03`, or `05`. Run `06_bass_energy.py` without a flag. These plots save to `analysis/website_plots/`.
