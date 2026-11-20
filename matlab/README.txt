EECS 351 preliminary song-transition baseline

Open preliminary_transition.m in MATLAB and click Run.
The default creates SYNTHETIC tones and beat pulses, not real songs.
It saves input waveforms, amplitude spectra, a linear crossfade, audio and data.

Verified in MATLAB R2026b: two 12-second inputs at 22050 Hz, 4-second overlap, 20-second output, peak 0.9. Finite samples, output duration and complementary fade gains passed checks.

This does NOT implement tempo estimation, beat alignment, pitch-preserving time stretch, bass swapping or perceptual loudness matching. Listening quality on songs remains untested.

For real audio: create a data folder, put equal-sample-rate WAV clips there named song_a.wav and song_b.wav, and change use_demo to false. Keep a copy of synthetic results before rerunning. The script takes the first 12 seconds and converts stereo to mono.

The script saves the figures, WAV files, MAT file, and run notes in the results folder beside the script.
