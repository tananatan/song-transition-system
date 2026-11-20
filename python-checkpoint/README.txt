SONG ANALYSIS: FIRST PYTHON CHECKPOINT
Install the packages in requirements.txt, then run python analyze_songs.py
from this folder to regenerate the three PNG figures in outputs.
On Windows, Run Analysis.bat and Edit Code.bat use a .venv in this folder.

Put the two full songs in the audio folder with the filenames given in the
repository README. See CREDITS.txt for the download links.
The script examines Something Elated 3:28-3:52 and Night Owl 0:00-0:24.
Change SONGS near the top to try other windows.

Code: reads audio; averages stereo to mono; calculates 50 ms RMS;
computes STFT (2048 samples, 512-sample hop); detects possible attacks from
increases in spectral magnitude; uses autocorrelation to suggest repeating
pulse rates between 60 and 180 BPM; saves plots and measurements.json.

Limits: RMS is signal level, not perceptual loudness. Mono averaging can
cancel stereo content. Waveform display skips samples; calculations use
all samples. Rhythm candidates are not verified tempo or beat positions.
Markers can include subdivisions/non-drum sounds. Listen before choosing
a beat. Spectrogram shows 0-4000 Hz only. Windows are manually picked.
This script does not choose an optimum, beatmatch, time-stretch or render
audio. Existing listening previews are separate.

Verified locally with Python 3.14.10 on this computer.

