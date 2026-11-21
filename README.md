# Song Transition System

For EECS 351, we're looking for a place to start an overlap between **Something Elated** and **Night Owl**. We study the end of the first song and the start of the second. A cue pair gives one timestamp in each song.

## Where the code is

- [`analysis/measurements/`](analysis/measurements/) has the numbered scripts for waveform and RMS level, frequency content, beat estimates, and bass. `song_tools.py` has the shared audio and measurement functions.
- [`analysis/rank_cues.py`](analysis/rank_cues.py) compares possible starts using frequency balance, bass overlap, attacks near beats, level changes, and harmony.

## Run it

Use Python 3.14. Save these Broke For Free tracks in `analysis/audio/` with the filenames shown.

- `Something_Elated.mp3` · [Download Something Elated](https://freemusicarchive.org/music/Broke_For_Free/Something_EP/Broke_For_Free_-_Something_EP_-_05_Something_Elated/) · [CC BY 3.0 US](https://creativecommons.org/licenses/by/3.0/us/)
- `Night_Owl.mp3` · [Download Night Owl](https://freemusicarchive.org/music/Broke_For_Free/Directionless_EP/Broke_For_Free_-_Directionless_EP_-_01_Night_Owl/) · [CC BY 3.0](https://creativecommons.org/licenses/by/3.0/)

```sh
python -m pip install -r requirements.txt
python analysis/measurements/01_waveform.py
python analysis/rank_cues.py
```

Run the commands from the repository folder. You can also run each script on its own in VS Code. The plots and cue results go in `analysis/plots/`.

Open `top_cues.csv` for the top three pairs and `cue_times.png` to see where the highest-scoring pair lands in the songs.

For the 20-second website plots, add `--website` when running script `01`, `02`, `03`, or `05`. Script `06` saves its bass plot there by default. These files go in `analysis/website_plots/`.
