# Song Transition System

EECS 351 project for analyzing songs and prototyping a transition between them.

| Folder | Contents |
| --- | --- |
| [`analysis/`](analysis/) | Current Python scripts for waveform, RMS signal level, spectrograms, beat estimates, FFT, and bass energy. |
| [`matlab/`](matlab/) | MATLAB linear crossfade demo with synthetic inputs. |
| [`python-checkpoint/`](python-checkpoint/) | Earlier Python analysis scripts and the combined `analyze_songs.py` workflow. |

## Run the Python analysis

Use Python 3.14 and run these commands from the repository root. The pinned analysis dependencies were checked with Python 3.14.10.

```powershell
py -3.14 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r analysis\requirements.txt
```

On macOS or Linux, use `python3.14 -m venv .venv` and replace the interpreter path in these commands with `.venv/bin/python`.

Download the two Broke For Free tracks from the links in [music credits](python-checkpoint/CREDITS.txt) and place them in `analysis/audio/` as `Something_Elated.mp3` and `Night_Owl.mp3`. Then run the first plot:

```powershell
.\.venv\Scripts\python.exe analysis\01_waveform_loudness.py
```

See the [analysis notes](analysis/README.txt) for the other scripts and their output locations. For the earlier checkpoint, install [`python-checkpoint/requirements.txt`](python-checkpoint/requirements.txt) and put the tracks in `python-checkpoint/audio/`.

## Run the MATLAB demo

Open [`matlab/preliminary_transition.m`](matlab/preliminary_transition.m) in MATLAB and click **Run**. The default synthetic example requires no audio files and saves its results under `matlab/results/`. See the [MATLAB notes](matlab/README.txt) for using your own WAV clips.
