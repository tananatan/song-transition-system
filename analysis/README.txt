EECS 351 Song Analysis
=====================

Follow the Python setup in the repository README. In VS Code, select the
repository's virtual environment as the Python interpreter, open a script,
and click Run Python File. The scripts find the tracks in analysis/audio/
and print the paths of their saved figures.

Plots
-----
01 shows the waveform and 50 ms RMS signal level.
02 shows spectrograms for the selected sections.
03 plots 20 ms RMS signal level and uses librosa to estimate the beats.
   Open plots/03_librosa_beats.png to see the beat markers.
04 shows a full-song spectrogram for each song.
05 shows a full-song, one-sided FFT for each song with frequency in Hz.

Scripts 01–03 use Something Elated at 208–232 s and Night Owl at 0–24 s.
RMS measures signal level. The beat markers and BPM in plot 03 are estimates
for the selected sections.

Website plot exports
--------------------
With the virtual environment active, run these from the repository root.

python analysis/01_waveform_loudness.py --website
python analysis/02_frequencies.py --website
python analysis/03_possible_beats.py --website
python analysis/05_full_fft.py --website
python analysis/06_bass_energy.py

Open website_plots in the VS Code Explorer to see the five PNGs. Each uses the
last 20 seconds of Something Elated and the first 20 seconds of Night Owl.
Time axes are measured from the beginning of each original song. The rhythm
PNG uses BPM estimates from the wider cue-search sections. Librosa uses
those estimates to track candidate beats within the 20-second excerpts.

The STFT panels share 0 to 4000 Hz and -80 to -10 dB re 1.
The 20-second spectra use a Hann window, divide by its sum, and use matching
axes through 22,050 Hz. Bass energy sums power from 30 to 250 Hz in each
short frame. Both bass panels use the same mean-square reference of 1.

Music credits
-------------
Both tracks are by Broke For Free and came from the Free Music Archive.

Something Elated (CC BY 3.0 US)
https://freemusicarchive.org/music/Broke_For_Free/Something_EP/Broke_For_Free_-_Something_EP_-_05_Something_Elated/
https://creativecommons.org/licenses/by/3.0/us/

Night Owl (CC BY 3.0)
https://freemusicarchive.org/music/Broke_For_Free/Directionless_EP/Broke_For_Free_-_Directionless_EP_-_01_Night_Owl/
https://creativecommons.org/licenses/by/3.0/
